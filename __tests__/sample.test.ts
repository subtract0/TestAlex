// Basic sample test to verify Jest setup
describe('Sample Tests', () => {
  test('should verify Jest is working', () => {
    expect(2 + 2).toBe(4);
  });

  test('should verify TypeScript support', () => {
    const message: string = 'Hello TypeScript';
    expect(message).toContain('TypeScript');
  });

  test('should verify async functionality', async () => {
    const promise = Promise.resolve(42);
    await expect(promise).resolves.toBe(42);
  });
});
