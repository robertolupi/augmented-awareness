package obsidian

import "strings"

func SkipCodeBlocks(content []string) []string {
	var result []string
	inCodeBlock := false

	for _, line := range content {
		if strings.HasPrefix(line, "```") {
			inCodeBlock = !inCodeBlock
			continue
		}
		if !inCodeBlock {
			result = append(result, line)
		}
	}

	return result
}
