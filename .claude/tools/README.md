# Toolbox

<!-- GENERATED FROM mapping.json BY tool_mapping.py — DO NOT EDIT BY HAND. -->
<!-- Regenerate: .claude/tools/tool_mapping.py readme                      -->

Deterministic scripts. No model involved: same input, same output, every time.

Agents should not read this file — it is for humans. Agents use
`tool_mapping.py list` and `tool_mapping.py get <key>`, which is cheaper than
parsing prose and cannot drift from the registry.

| key | what it does | use when |
|---|---|---|
| `arch-map` | Where code lives: slices, paths, owned classes, dependency rules | before searching the tree for anything — locate by slice instead of globbing |
| `check-issue` | Validate a local issue file: Gherkin, tier, constraints, outcome | before starting work from a markdown ticket, or in CI on issue open |
| `coverage-gaps` | Uncovered lines, scoped to the files changed on this branch | the coverage gate failed, or you need to know what is untested in your diff |
| `issue-context` | GitHub issue -> validated work brief; refuses bad tickets, stops on tier-3 | step 1 of /work, always, before any planning or code |
| `mutation-survivors` | Surviving mutants and where they are, in ~15 lines | after -Pmutation, or whenever asked to improve the mutation score |

## Adding a tool

```bash
.claude/tools/tool_mapping.py register \
  --key my-tool --path .claude/tools/my_tool.py \
  --summary "one line" --use-when "the situation that calls for it"
.claude/tools/tool_mapping.py readme    # regenerate this file
```

`tool_mapping.py check` runs in pre-push and fails if a tool exists on disk but
is not registered. An unregistered tool is an undiscoverable tool.
