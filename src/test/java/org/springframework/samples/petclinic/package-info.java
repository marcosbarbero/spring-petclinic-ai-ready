/**
 * Testing strategy.
 *
 * <p>
 * Every layer below answers a different question. They are not redundant, and a gap in
 * one is not covered by another being green. This file exists because "we have tests" is
 * not a strategy — knowing which question each test answers is.
 *
 * <h2>What we run</h2>
 *
 * <table border="1">
 * <caption>Test types in this repository</caption>
 * <tr>
 * <th>Type</th>
 * <th>Question it answers</th>
 * <th>Where</th>
 * </tr>
 *
 * <tr>
 * <td><b>Unit</b></td>
 * <td>Does this class do the right thing in isolation?</td>
 * <td>{@code owner/PetValidatorTests}, {@code owner/OwnerTests}, {@code vet/VetTests} —
 * plain JUnit 5 + AssertJ, no Spring context.</td>
 * </tr>
 *
 * <tr>
 * <td><b>Web slice</b></td>
 * <td>Does the HTTP edge bind, validate and route correctly?</td>
 * <td>{@code @WebMvcTest} — {@code owner/OwnerControllerTests},
 * {@code owner/PetControllerTests}. Never {@code @SpringBootTest} for this.</td>
 * </tr>
 *
 * <tr>
 * <td><b>Integration</b></td>
 * <td>Does it work against a real database and a real context?</td>
 * <td>{@code PetClinicIntegrationTests}, and the Docker-backed
 * {@code MySqlIntegrationTests} / {@code PostgresIntegrationTests}, which are
 * <b>opt-in</b> via {@code -Pcontainers} so a clone without Docker still goes green.</td>
 * </tr>
 *
 * <tr>
 * <td><b>Architecture</b></td>
 * <td>Does the code still have the shape we agreed on?</td>
 * <td>{@code architecture/ArchitectureRulesTest} — 8 ArchUnit rules. This is what turns
 * "please respect the package boundaries" from a code-review comment into a build
 * failure.</td>
 * </tr>
 *
 * <tr>
 * <td><b>Coverage</b></td>
 * <td>Did a test <i>execute</i> this line?</td>
 * <td>JaCoCo, gated at 90% line / 78% branch in {@code verify}.</td>
 * </tr>
 *
 * <tr>
 * <td><b>Mutation</b></td>
 * <td>Would any test <i>notice</i> if this line changed?</td>
 * <td>PIT, gated at 80% via {@code -Pmutation}. Coverage proves a line ran; mutation
 * proves it was checked. A suite can have 100% coverage and a 0% mutation score — that
 * suite is decoration.</td>
 * </tr>
 * </table>
 *
 * <h2>What we do NOT have, and why</h2>
 *
 * <p>
 * Named deliberately. An unstated gap gets mistaken for coverage.
 *
 * <h3>Contract tests — absent, and correctly so</h3>
 *
 * <p>
 * Contract testing (Pact, Spring Cloud Contract) proves that a producer and a consumer
 * still agree about a payload after either side changes independently. It needs two
 * independently deployable sides to be worth anything.
 *
 * <p>
 * PetClinic is a single-module monolith. There is no network boundary here, no second
 * team, and nothing that can be deployed separately — so a contract test would assert
 * that this module agrees with itself, which the compiler already guarantees. Adding one
 * would be ceremony that looks like rigour.
 *
 * <p>
 * <b>In a real service it belongs at tier 2 and above</b>, on every synchronous API and
 * every published event: the provider verifies the consumer's expectations in its own
 * pipeline, so breaking a consumer fails the <i>provider's</i> build rather than
 * someone's afternoon. That is the same author-blind principle as everything else here —
 * it just needs a boundary to apply to.
 *
 * <h3>End-to-end tests — absent, and worth adding</h3>
 *
 * <p>
 * A real E2E test drives the running application the way a person does: start the app,
 * open the new-pet form in a browser, submit a future birth date, assert the rendered
 * error. Playwright or Selenium against {@code ./mvnw spring-boot:run}.
 *
 * <p>
 * Nothing above proves the <i>journey</i> works. {@code @WebMvcTest} proves the
 * controller binds; it does not prove the Thymeleaf template renders the error where a
 * user can see it. Both can be green while the page is blank.
 *
 * <p>
 * E2E stays deliberately thin — a handful of critical journeys, not a mirror of the unit
 * suite. They are the slowest and flakiest tests you own, so every one you add has to
 * earn its place. Run them in CI, never in the pre-push gate.
 *
 * <h2>The rule</h2>
 *
 * <p>
 * Push each check to the fastest layer that can answer the question. Validation logic
 * belongs in a unit test, not an E2E test that takes 30 seconds to tell you the same
 * thing. Reserve the slow layers for what only they can prove.
 */
package org.springframework.samples.petclinic;
