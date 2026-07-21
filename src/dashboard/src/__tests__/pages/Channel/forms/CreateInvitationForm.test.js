/*
 SPDX-License-Identifier: Apache-2.0
 */
import {
  validateOrganizations,
  normalizeRequiredSignatures,
} from '../../../../pages/Channel/forms/CreateInvitationForm';

describe('validateOrganizations', () => {
  it('rejects empty array', () => {
    expect(validateOrganizations([])).toBe(false);
  });
  it('rejects non-array', () => {
    expect(validateOrganizations(null)).toBe(false);
    expect(validateOrganizations(undefined)).toBe(false);
    expect(validateOrganizations('o1')).toBe(false);
  });
  it('accepts single-element array', () => {
    expect(validateOrganizations(['o1'])).toBe(true);
  });
  it('accepts multi-element array', () => {
    expect(validateOrganizations(['o1', 'o2', 'o3'])).toBe(true);
  });
});

describe('normalizeRequiredSignatures', () => {
  it('returns undefined when value is empty', () => {
    expect(normalizeRequiredSignatures(undefined)).toBeUndefined();
    expect(normalizeRequiredSignatures(null)).toBeUndefined();
    expect(normalizeRequiredSignatures('')).toBeUndefined();
  });
  it('returns undefined when value is a non-integer string', () => {
    expect(normalizeRequiredSignatures('foo')).toBeUndefined();
  });
  it('returns undefined when value is 0 or negative', () => {
    expect(normalizeRequiredSignatures(0)).toBeUndefined();
    expect(normalizeRequiredSignatures(-1)).toBeUndefined();
  });
  it('returns integer when value is a positive integer', () => {
    expect(normalizeRequiredSignatures(1)).toBe(1);
    expect(normalizeRequiredSignatures(5)).toBe(5);
  });
  it('accepts numeric strings and coerces to integer', () => {
    expect(normalizeRequiredSignatures('3')).toBe(3);
  });
  it('returns undefined when value exceeds the max bound', () => {
    expect(normalizeRequiredSignatures(5, 4)).toBeUndefined();
  });
  it('returns value when value equals the max bound', () => {
    expect(normalizeRequiredSignatures(4, 4)).toBe(4);
  });
  it('ignores max when max is undefined', () => {
    expect(normalizeRequiredSignatures(100)).toBe(100);
  });
});
