# Architecture

<!-- GENERATED FROM mapping.json BY .claude/tools/arch_map.py — DO NOT EDIT. -->
<!-- Regenerate: .claude/tools/arch_map.py readme                            -->

**Package by feature (vertical slices)**

Each feature slice owns its entities, controllers, repositories and validators. Not layered: there is no controller/ service/ repository/ split.

Decision: [docs/adr/0001-package-by-feature.md](0001-package-by-feature.md)  ·  Enforced by: `ArchitectureRulesTest.java`

Agents should not read this file — it is for humans. Agents use
`.claude/tools/arch_map.py get <slice>`, which is cheaper and cannot drift.

| slice | responsibility | may depend on | must not |
|---|---|---|---|
| `model` | Shared kernel. Base types every slice builds on. No business rules of its own. | — | owner, vet, system, org.springframework.web, jakarta.servlet |
| `owner` | Owners, their pets, and pet visits. Everything a clinic customer touches. | model | vet |
| `system` | Cross-cutting web and cache configuration, error pages, welcome page. | model | — |
| `vet` | Veterinarians and their specialties. | model | owner |

## Slices

### `model`

- package: `org.springframework.samples.petclinic.model`
- source: `src/main/java/org/springframework/samples/petclinic/model`
- tests: `src/test/java/org/springframework/samples/petclinic/model`
- owns: `BaseEntity`, `NamedEntity`, `Person`

> A dependency from here into a feature slice inverts the whole structure. Also must stay usable without a servlet container.

### `owner`

- package: `org.springframework.samples.petclinic.owner`
- source: `src/main/java/org/springframework/samples/petclinic/owner`
- tests: `src/test/java/org/springframework/samples/petclinic/owner`
- owns: `Owner`, `Pet`, `PetType`, `Visit`, `OwnerController`, `PetController`, `VisitController`, `OwnerRepository`, `PetTypeRepository`, `PetValidator`, `PetTypeFormatter`

> Pet form validation lives in PetValidator, NOT as annotations on the Pet entity - the entity is shared with the import path.

### `system`

- package: `org.springframework.samples.petclinic.system`
- source: `src/main/java/org/springframework/samples/petclinic/system`
- tests: `src/test/java/org/springframework/samples/petclinic/system`
- owns: `CacheConfiguration`, `CrashController`, `WebConfiguration`, `WelcomeController`

> Infrastructure, not a feature. Do not put business rules here.

### `vet`

- package: `org.springframework.samples.petclinic.vet`
- source: `src/main/java/org/springframework/samples/petclinic/vet`
- tests: `src/test/java/org/springframework/samples/petclinic/vet`
- owns: `Vet`, `Vets`, `Specialty`, `VetController`, `VetRepository`

> Vets and owners are deliberately unaware of each other. If a feature seems to need both, that is a design conversation.
