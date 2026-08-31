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
import org.springframework.validation.FieldError;
import org.springframework.validation.MapBindingResult;

import java.time.LocalDate;
import java.util.HashMap;

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

	private static final int MAX_NAME_LENGTH = 50;

	private static final int PREVIOUS_MAX_NAME_LENGTH = 30;

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
	void acceptsNameOfExactlyMaximumLength() {
		validateWithName("A".repeat(MAX_NAME_LENGTH));

		assertFalse(errors.hasFieldErrors("name"));
	}

	@Test
	void rejectsNameLongerThanMaximum() {
		validateWithName("A".repeat(MAX_NAME_LENGTH + 1));

		assertThat(errors.getFieldError("name")).isNotNull().extracting(FieldError::getCode).isEqualTo("size");
	}

	@Test
	void acceptsOrdinaryName() {
		validateWithName("Leo");

		assertFalse(errors.hasFieldErrors("name"));
	}

	@Test
	void acceptsNameOfPreviousMaximumLength() {
		validateWithName("A".repeat(PREVIOUS_MAX_NAME_LENGTH));

		assertFalse(errors.hasFieldErrors("name"));
	}

	@Test
	void rejectsBlankNameAsRequired() {
		validateWithName("");

		assertThat(errors.getFieldError("name")).isNotNull().extracting(FieldError::getCode).isEqualTo("required");
	}

	/**
	 * Validates a pet that is valid in every respect except, possibly, its name, so that
	 * "name" is the only field under test.
	 */
	private void validateWithName(String name) {
		petType.setName(petTypeName);
		pet.setName(name);
		pet.setType(petType);
		pet.setBirthDate(petBirthDate);

		petValidator.validate(pet, errors);
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
			pet.setName("A".repeat(MAX_NAME_LENGTH + 1));
			pet.setType(petType);
			pet.setBirthDate(petBirthDate);

			petValidator.validate(pet, errors);

			assertTrue(errors.hasFieldErrors("name"));
		}

	}

}
