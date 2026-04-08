# Sandbox Implementation Reference

> Sources: Codex CLI (Seatbelt/Landlock/bwrap), OpenHands (Docker sandbox) source-level implementations

## Sandbox Policy Types [CX]

Codex CLI defines four policy levels, from permissive to strict:

```rust
enum SandboxPolicy {
    // Full access — unrestricted; dev/debug only; never production
    DangerFullAccess,

    // Read-only — read-only filesystem + no network
    // Applicable: pure code analysis, search
    ReadOnly,

    // Workspace write — writable workspace directory, read-only elsewhere
    // Applicable: most coding agent scenarios
    WorkspaceWrite,

    // External sandbox — delegated to external sandbox manager
    // Applicable: custom sandbox environments
    ExternalSandbox,
}
```

**Automatic policy rule conversion**: Upper-layer allow/deny rules can auto-generate sandbox configuration:
```
allow: FileEdit(path:/project/src/**) → writable_paths: ["/project/src/"]
deny: network → network_allowed: false
```

---

## macOS: Seatbelt (sandbox-exec) [CX]

Codex CLI uses Seatbelt (Apple kernel sandbox) on macOS, defining policy via SBPL (Sandbox Profile Language).

### Implementation Architecture

```
Codex CLI
    ↓
Generate SBPL policy file (~850 lines of Rust generation)
    ↓
sandbox-exec -f policy.sb -- /bin/bash -c "command"
    ↓
Kernel-level interception: file/network/process/IPC
```

### SBPL Policy Structure

```scheme
(version 1)

;; Default deny everything
(deny default)

;; Allow reading system libraries (all commands need these)
(allow file-read*
    (subpath "/usr/lib")
    (subpath "/usr/share")
    (subpath "/System/Library"))

;; Allow reading project directory
(allow file-read*
    (subpath "/Users/dev/project"))

;; Allow writing specific directories
(allow file-write*
    (subpath "/Users/dev/project/src")
    (subpath "/tmp"))

;; Allow executing specific binaries
(allow process-exec
    (literal "/bin/bash")
    (literal "/usr/bin/git")
    (literal "/usr/local/bin/node"))

;; Network policy
(allow network-outbound
    (remote tcp "*:443"))   ;; HTTPS only
```

### Key Implementation Details

1. **System dependency paths**: Must allow reading `/usr/lib`, `/dev/urandom`, etc., otherwise commands can't start
2. **Dynamic linker**: `/usr/lib/dyld` must be executable
3. **Temporary files**: `/tmp` and `$TMPDIR` typically need write permissions
4. **Homebrew paths**: `/opt/homebrew/` or `/usr/local/` need read permissions
5. **Semaphores**: Some tools need `ipc-posix-shm-read*` permissions

### Limitations

- macOS only
- Apple hasn't published complete SBPL documentation (requires reverse engineering + experimentation)
- `sandbox-exec` is a deprecated API (but still works)
- No cgroup-level resource limits (CPU/memory)

---

## Linux: Landlock LSM [CX]

Landlock is a Linux 5.13+ kernel security module allowing unprivileged processes to self-restrict filesystem access.

### Implementation Architecture

```
Codex CLI
    ↓
Create Landlock ruleset (syscall)
    ↓
Add rules (readable paths, writable paths)
    ↓
landlock_restrict_self() — irreversible; applies to current process and children
    ↓
exec("bash", "-c", "command")
```

### Rust Implementation Key Points

```rust
use landlock::{
    Access, AccessFs, PathBeneath, PathFd, Ruleset, RulesetAttr,
    RulesetCreatedAttr, ABI,
};

fn sandbox_command(cmd: &str, policy: &SandboxPolicy) -> Result<()> {
    let abi = ABI::V3;  // Linux 6.2+

    let mut ruleset = Ruleset::default()
        .handle_access(AccessFs::from_all(abi))?
        .create()?;

    // Add read-only paths
    for path in &policy.readable_paths {
        ruleset = ruleset.add_rule(PathBeneath::new(
            PathFd::new(path)?,
            AccessFs::from_read(abi),
        ))?;
    }

    // Add writable paths
    for path in &policy.writable_paths {
        ruleset = ruleset.add_rule(PathBeneath::new(
            PathFd::new(path)?,
            AccessFs::from_all(abi),
        ))?;
    }

    // Apply restrictions (irreversible)
    ruleset.restrict_self()?;

    // Execute command
    Command::new("bash").arg("-c").arg(cmd).exec()
}
```

### Key Details

1. **ABI versions**: V1 (5.13) / V2 (5.19) / V3 (6.2) / V4 (6.7); higher = more access types
2. **Irreversible**: Cannot undo after `restrict_self()`; child processes inherit restrictions
3. **Network restriction**: ABI V4+ supports `AccessNet` (TCP bind/connect); lower versions no network restriction
4. **Fallback**: Need fallback to bwrap or no-sandbox when kernel doesn't support it

---

## Linux Alternative: bubblewrap (bwrap) [CX]

Used when Landlock unavailable (older kernels), bwrap (Flatpak's sandbox tool).

### Implementation

```bash
bwrap \
    --ro-bind /usr /usr \
    --ro-bind /lib /lib \
    --ro-bind /lib64 /lib64 \
    --ro-bind /bin /bin \
    --ro-bind /etc/resolv.conf /etc/resolv.conf \
    --bind /home/user/project/src /home/user/project/src \
    --tmpfs /tmp \
    --proc /proc \
    --dev /dev \
    --unshare-net \          # Isolate network (optional)
    --die-with-parent \      # Kill child when parent exits
    -- bash -c "command"
```

### Landlock vs bwrap Comparison

| Feature | Landlock | bwrap |
|------|----------|-------|
| Kernel requirement | 5.13+ | Any (userspace) |
| Privilege needed | None | None (userspace namespace) |
| Network restriction | ABI V4+ | Supported (`--unshare-net`) |
| Latency | ~0ms | ~5ms (namespace creation) |
| Process isolation | No (same namespace) | Yes (separate namespace) |
| PID isolation | No | Yes (`--unshare-pid`) |

**Recommendation**: Prefer Landlock (zero latency); fallback to bwrap when Landlock unavailable.

---

## Windows: Windows Sandbox

Windows Sandbox provides lightweight virtualization isolation:

```xml
<!-- sandbox-config.wsb -->
<Configuration>
    <MappedFolders>
        <MappedFolder>
            <HostFolder>C:\project\src</HostFolder>
            <SandboxFolder>C:\src</SandboxFolder>
            <ReadOnly>false</ReadOnly>
        </MappedFolder>
    </MappedFolders>
    <Networking>Disable</Networking>
    <LogonCommand>
        <Command>cmd /c "command"</Command>
    </LogonCommand>
</Configuration>
```

**Limitations**: Startup latency ~500ms+, requires Windows Pro/Enterprise; not suitable for high-frequency invocations.

---

## Docker Sandbox [OH]

OpenHands supports 4 Runtime Backends; Docker is one:

| Backend | Use Case | Characteristics |
|---------|---------|------|
| **Docker** (aka eventstream) | Production | Full isolation; network/filesystem controlled |
| **Remote** | Distributed deployment | Connect to remote Docker host |
| **Local** | Local dev/debug | Run directly on host; no isolation |
| **Kubernetes** | K8s cluster | Pod-level isolation |
| **CLI** | Lightweight CLI mode | Minimal runtime |
| **E2B** (third-party) | Cloud sandbox | E2B Cloud Sandbox; start/stop on demand |

Docker mode specific implementation:

### Architecture

```
OpenHands Server (host)
    │
    ├── EventStream (bidirectional communication)
    │       ↕
    ├── Runtime Container (Docker)
    │   ├── /openhands/        # Agent runtime code
    │   ├── /workspace/        # User project (mounted)
    │   ├── bash server        # Command execution service
    │   └── jupyter server     # Code execution service
    │
    └── Multiple Runtime backends:
        ├── EventStreamRuntime  (Docker, default)
        ├── RemoteRuntime       (remote Docker)
        └── E2BRuntime          (E2B cloud)
```

### Key Design Points

1. **EventStream communication**: Host and container communicate via event stream; don't share process space directly
2. **Mount control**: Only `/workspace` is mounted; rest of filesystem isolated within container
3. **User isolation**: Runs as non-root user inside container
4. **Resource limits**: Docker `--memory` `--cpus` for resource constraints
5. **Network policy**: Container network configurable (host/bridge/none)

### Runtime Selection

| Runtime | Isolation | Latency | Cost | Use |
|---------|---------|------|------|------|
| EventStream (Docker) | High | ~200ms | Self-hosted | Dev/self-hosted |
| Remote Docker | High | ~300ms | VPS | Team/CI |
| E2B Cloud | Highest | ~500ms | Pay-per-use | SaaS product |

---

## Sandbox Selection Decision Tree

```
What platform does your Agent run on?
├── macOS → Seatbelt
├── Linux
│   ├── Kernel ≥ 5.13 → Landlock (preferred)
│   ├── Kernel < 5.13 → bwrap
│   └── Need full isolation → Docker
├── Windows → Windows Sandbox
├── Multi-platform → Abstraction layer + platform detection
└── SaaS → E2B Cloud / Docker Remote
```

**Implementation advice**: Define `SandboxBackend` trait/interface; detect platform at runtime to select implementation.
