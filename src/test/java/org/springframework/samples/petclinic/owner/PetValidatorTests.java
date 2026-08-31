/*
 * Copyright 2012-2024 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.springframework.samples.petclinic.owner;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.validation.Errors;
import org.springframework.validation.MapBindingResult;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Test class for {@link PetValidator}
 *
 * @author Wick Dynex
 */
@ExtendWith(MockitoExtension.class)
@DisabledInNativeImage
class PetValidatorTests {

	private PetValidator petValidator;

	private Pet pet;

	private PetType petType;

	private Errors errors;

	private static final String petName = "Buddy";

	private static final String petTypeName = "Dog";

	private static final LocalDate petBirthDate = LocalDate.of(1990, 1, 1);

	@BeforeEach
	void setUp() {
		petValidator = new PetValidator();
		pet = new Pet();
		petType = new PetType();
		errors = new MapBindingResult(new HashMap<>(), "pet");
	}

	@Test
	void supportsPetClass() {
		assertTrue(petValidator.supports(Pet.class));
	}

	@Test
	void doesNotSupportNonPetClass() {
		assertFalse(petValidator.supports(String.class));
	}

	@Test
	void validate() {
		petType.setName(petTypeName);
		pet.setName(petName);
		pet.setType(petType);
		pet.setBirthDate(petBirthDate);

		petValidator.validate(pet, errors);

		assertFalse(errors.hasErrors());
	}

	@Test
	void acceptsBirthDateInThePast() {
		givenValidPetWithBirthDate(LocalDate.of(2020, 1, 15));

		petValidator.validate(pet, errors);

		assertThat(errors.hasFieldErrors("birthDate")).isFalse();
	}

	@Test
	void acceptsBirthDateOfToday() {
		givenValidPetWithBirthDate(LocalDate.now());

		petValidator.validate(pet, errors);

		assertThat(errors.hasFieldErrors("birthDate")).isFalse();
	}

	private void givenValidPetWithBirthDate(LocalDate birthDate) {
		petType.setName(petTypeName);
		pet.setName("Leo");
		pet.setType(petType);
		pet.setBirthDate(birthDate);
	}

	private List<String> errorCodesOnBirthDate() {
		return errors.getFieldErrors("birthDate")
			.stream()
			.flatMap(fieldError -> Arrays.stream(fieldError.getCodes()))
			.toList();
	}

	@Nested
	class ValidateHasErrors {

		@Test
		void validateWithInvalidPetName() {
			petType.setName(petTypeName);
			pet.setName("");
			pet.setType(petType);
			pet.setBirthDate(petBirthDate);

			petValidator.validate(pet, errors);

			assertTrue(errors.hasFieldErrors("name"));
		}

		@Test
		void validateWithInvalidPetType() {
			pet.setName(petName);
			pet.setType(null);
			pet.setBirthDate(petBirthDate);

			petValidator.validate(pet, errors);

			assertTrue(errors.hasFieldErrors("type"));
		}

		@Test
		void validateWithInvalidBirthDate() {
			petType.setName(petTypeName);
			pet.setName(petName);
			pet.setType(petType);
			pet.setBirthDate(null);

			petValidator.validate(pet, errors);

			assertTrue(errors.hasFieldErrors("birthDate"));
		}

		@Test
		void validateWithLongPetName() {
			petType.setName(petTypeName);
			pet.setName("A".repeat(31));
			pet.setType(petType);
			pet.setBirthDate(petBirthDate);

			petValidator.validate(pet, errors);

			assertTrue(errors.hasFieldErrors("name"));
		}

		@Test
		void rejectsBirthDateInTheFuture() {
			givenValidPetWithBirthDate(LocalDate.now().plusDays(1));

			petValidator.validate(pet, errors);

			assertThat(errorCodesOnBirthDate()).contains("typeMismatch.birthDate");
		}

		@Test
		void rejectsMissingBirthDateAsRequired() {
			givenValidPetWithBirthDate(null);

			petValidator.validate(pet, errors);

			assertThat(errorCodesOnBirthDate()).contains("required").doesNotContain("typeMismatch.birthDate");
		}

	}

}
