# Agents Configuration Guide (`agents.md`)

This file defines global, cross-project preferences for GPT-Codex and any sub-agents it may spin up.  
Project-specific logic, rules, schemas, and domain constraints must always be declared in the companion `spec.md` inside each repository.

---

## 1. Core Intent

Codex should function as a disciplined, multi-agent coding system that:
- Builds reproducible, human-readable, maintainable software.
- Follows explicit rules.
- Generates **no compiled artifacts**, no binaries, no `__pycache__`, no `.class`, no temporary machine outputs.
- Never adds hidden files.
- Produces only source files, documentation, and deterministic assets.

All configuration, prompts, and environment tuning should remain transparent and editable.

---

## 2. My Standing Preferences for Code Generation

Codex and its sub-agents must assume the following defaults unless overridden by a project’s `spec.md`:

### 2.1 Code Style & Structure
- Prefer **clean, modular architectures**.
- Use **predictable directory structures**.
- Include **clear comments**, but avoid noise.
- When building CLIs, services, containers, or GUIs, generate:
  - Self-contained modules  
  - A minimal dependency footprint  
  - Tooling scripts that work locally without cloud services

### 2.2 Documentation Requirements
Every delivered feature must include:
- A concise explanation of intent
- Setup instructions
- A short “why this design” section
- Any assumptions Codex made

Prefer Markdown; avoid HTML unless required.

### 2.3 Environment Rules
- Never rely on system-wide state that must be guessed.
- If a tool requires installation (pip, apt, blender addon, piper, etc.) list the exact commands.
- For GUIs, provide configuration panels so users don’t edit config files manually.

### 2.4 Safety & Reproducibility
- Always regenerate missing files deterministically.
- Never reference files that don’t exist.
- Avoid proprietary dependencies unless permitted in `spec.md`.

---

## 3. Sub-Agent Behavior

Codex may create sub-agents when parallelizable tasks exist, but must obey:
- Sub-agents shall inherit **all rules in this file** automatically.
- Sub-agents shall not create overlapping changes without producing a merge plan.
- No sub-agent may produce compiled outputs or binary artifacts.

Parallelism should be used for:
- Independent module generation  
- Documentation creation  
- Testing frameworks  
- GUI vs backend development  
- Code scanning / refactoring passes

Not for:
- Data downloads
- Network calls unless explicitly allowed in `spec.md`

---

## 4. File Generation Constraints

Codex must observe the following constraints:

### Forbidden Outputs  
- any binaries  
- any compiled artifacts  
- `.exe`, `.dll`, `.pyc`, `.o`, `.wasm`, etc.  
- auto-generated asset caches  
- vendor blobs unless approved in `spec.md`

### Required Outputs  
- Pure source files  
- Markdown documentation  
- Templates  
- Config files  
- Build/run scripts  
- Unit tests  
- GUI configuration interfaces where relevant  

---

## 5. Interaction Model (How Codex Should Work in This Repo)

When Codex is invoked:

1. **Read `agents.md` first**  
   Apply all global preferences.

2. **Then read `spec.md`**  
   This defines:
   - Project scope  
   - File trees  
   - Build system choices  
   - Naming conventions  
   - Allowed dependencies  
   - GUI requirements  
   - APIs  
   - Test coverage rules  

3. **Construct a work plan**  
   Outline architecture before generating code.

4. **Generate concise, self-contained modules**  
   No dead ends.  
   No half-implemented stubs unless explicitly marked TODO.

5. **Update README & relevant docs**  
   Codex must keep documentation synchronized with actual code.

---

## 6. Enforcement Rules

Codex should:
- Validate its own output before presenting it.
- Refuse to generate binaries.
- Refuse ambiguous operations.
- Warn when assumptions are being made.
- Stop and request clarification only if the spec contradicts itself.

---

## 7. Extension Points

Additional preferences may be defined in:
- `spec.md` (project-specific architecture)
- `config/` directory (runtime parameters)
- `addons/` directory (extensions, plugins)

---

## 8. Final Notes

This `agents.md` file is deliberately **project-agnostic**.  
Every repo using this pattern must include its own `spec.md`, which becomes the single source of truth for what Codex builds.

Codex must follow:
1. This file → 2. The project’s `spec.md` → 3. The user's new instructions (if any)

---
