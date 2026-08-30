package org.springframework.samples.petclinic.architecture;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.fields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

/**
 * Architecture rules, enforced as tests.
 * <p>
 * This is the harness gate that answers the most common complaint about AI-generated
 * code: "it violates our package boundaries". It cannot violate a boundary that fails the
 * build. Neither can a human, which is the point — these rules are author-blind.
 * <p>
 * PetClinic is organised <em>package by feature</em> ({@code owner}, {@code vet},
 * {@code system}) rather than package by layer, so the valuable rules here are about
 * feature isolation, not about layering. See {@code docs/adr/0001-package-by-feature.md}.
 */
@AnalyzeClasses(packages = ArchitectureRulesTest.ROOT, importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureRulesTest {

	static final String ROOT = "org.springframework.samples.petclinic";

	/**
	 * The headline rule. Feature slices are independent: if {@code owner} needs something
	 * from {@code vet}, that is a design conversation, not a quiet import.
	 */
	@ArchTest
	static final ArchRule features_are_independent = SlicesRuleDefinition.slices()
		.matching(ROOT + ".(owner|vet)..")
		.should()
		.notDependOnEachOther()
		.because("feature slices must stay independent; cross-feature reuse belongs in model or a new shared slice");

	/**
	 * The shared kernel must not know about the features that build on it. This is the
	 * rule an agent breaks most often, because adding an import is always the shortest
	 * path to making something compile.
	 */
	@ArchTest
	static final ArchRule model_knows_nothing_about_features = noClasses().that()
		.resideInAPackage(ROOT + ".model..")
		.should()
		.dependOnClassesThat()
		.resideInAnyPackage(ROOT + ".owner..", ROOT + ".vet..", ROOT + ".system..")
		.because("model is the shared kernel; a dependency here inverts the whole structure");

	@ArchTest
	static final ArchRule no_package_cycles = SlicesRuleDefinition.slices()
		.matching(ROOT + ".(*)..")
		.should()
		.beFreeOfCycles();

	/** Repositories are Spring Data contracts, never hand-rolled classes. */
	@ArchTest
	static final ArchRule repositories_are_interfaces = classes().that()
		.haveSimpleNameEndingWith("Repository")
		.should()
		.beInterfaces()
		.because("repositories are declarative Spring Data contracts, not implementations");

	@ArchTest
	static final ArchRule repositories_live_in_feature_packages = classes().that()
		.haveSimpleNameEndingWith("Repository")
		.should()
		.resideInAnyPackage(ROOT + ".owner..", ROOT + ".vet..")
		.because("a repository belongs to exactly one feature slice");

	/**
	 * Constructor injection only. Field injection hides dependencies, makes classes
	 * untestable without a container, and is the default an agent reaches for.
	 */
	@ArchTest
	static final ArchRule no_field_injection = fields().should()
		.notBeAnnotatedWith("org.springframework.beans.factory.annotation.Autowired")
		.because("constructor injection only — field injection hides dependencies and blocks plain unit tests");

	/** Controllers are a web concern and belong nowhere else. */
	@ArchTest
	static final ArchRule controllers_are_web_only = classes().that()
		.haveSimpleNameEndingWith("Controller")
		.should()
		.resideInAnyPackage(ROOT + ".owner..", ROOT + ".vet..", ROOT + ".system..")
		.andShould()
		.beTopLevelClasses()
		.because("controllers are the web edge of a feature slice");

	/**
	 * Entities must not reach the web layer. Catches the "just pass the request into the
	 * entity" shortcut.
	 */
	@ArchTest
	static final ArchRule domain_types_stay_off_the_web = noClasses().that()
		.resideInAPackage(ROOT + ".model..")
		.should()
		.dependOnClassesThat()
		.resideInAnyPackage("org.springframework.web..", "jakarta.servlet..")
		.because("domain types must be usable without a servlet container");

}
