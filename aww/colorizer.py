import matplotlib.colors as mcolors
import matplotlib.pyplot as plt


def get_color_for_cluster(cluster_id):
    """Generates a consistent color for a cluster ID."""
    if cluster_id == -1:
        return ""  # No color for noise
    # Simple color rotation
    colors = ["#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#A0C4FF", "#BDB2FF", "#FFC6FF"]
    return colors[cluster_id % len(colors)]


def colorize_markdown(original_content, sentences, cluster_labels):
    """Injects HTML color tags into the markdown based on sentence clusters."""
    modified_content = original_content
    for i, sentence in enumerate(sentences):
        cluster_id = cluster_labels[i]
        color = get_color_for_cluster(cluster_id)
        if color:
            # Important: Replace only the first occurrence in case of duplicate sentences
            modified_content = modified_content.replace(
                sentence,
                f'<span style="background-color: {color};">{sentence}</span>',
                1
            )
    return modified_content


def build_palette(size: int, cmap_name: str) -> list[str]:
    cmap = plt.get_cmap(cmap_name)
    return [mcolors.to_hex(cmap(0.2 + 0.8 * i / max(size - 1, 1))) for i in range(size)]


def build_palette_map(lists: list[list[str]], cmaps: list[str]) -> dict[str, str]:
    palette = {}
    for lst, cmap in zip(lists, cmaps):
        p = build_palette(len(lst), cmap)
        for i, col in zip(lst, p):
            palette[i] = col
    return palette
