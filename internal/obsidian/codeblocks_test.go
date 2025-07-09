package obsidian

import "testing"

func TestSkipCodeBlocks(t *testing.T) {
	pageContent := []string{
		"# Test Page",
		"",
		"Some introductory text.",
		"```python",
		"print('Hello, World!')",
		"```",
	}

	result := SkipCodeBlocks(pageContent)
	if len(result) != 3 {
		t.Errorf("Expected 3 lines after skipping code blocks, got %d", len(result))
	}
}
