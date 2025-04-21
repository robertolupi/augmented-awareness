module Obsidian

using Markdown
using YAML

export Vault, Page, pages, frontmatter, pagecontent

"""
Access the Obsidian vault at the given path.

The vault is a directory containing markdown files and other resources.
"""
struct Vault
    path::String

    function Vault(path::String)
        path = expanduser(path)
        if !isdir(path) || !isdir(joinpath(path, ".obsidian"))
            error("The path $path provided is not an Obsidian Vault.")
        end
        new(path)
    end
end

"""
A page in an Obsidian vault.
"""
struct Page
    path::String
end

"""
pages(vault::Vault) :: Dict{String, Page}

    Return all pages in an obsidian vault.
"""
function pages(vault::Vault) :: Dict{String, Page}
    # Recursively get all markdown pages in the vault
    pages = Dict{String, Page}()
    for (dirpath, dirnames, filenames) in walkdir(vault.path)
        for filename in filenames
            if endswith(filename, ".md")
                filepath = joinpath(dirpath, filename)
                page = Page(filepath)
                pages[replace(filename, r"\.md$" => "")] = page
            end
        end
    end
    return pages
end


"""
readpage(page::Page) :: Tuple{String, String}

    Read the content of a page and return the frontmatter and content.
"""
function readpage(page::Page) :: Tuple{String, String}
    open(page.path, "r") do f
        content = read(f, String)
        # Split the content into frontmatter and body
        if startswith(content, "---\n")
            frontmatter_end = findfirst("---\n", content[4:end])
            if frontmatter_end === nothing
                error("Invalid frontmatter in file: $(page.path)")
            end
            frontmatter = content[5:frontmatter_end.start + 1 + 5 - 4]
            body = content[frontmatter_end.stop + 4:end]
        else
            frontmatter = ""
            body = content
        end
        return (frontmatter, body)
    end
end


"""
frontmatter(page::Page) :: Dict{String, Any}

    Return the frontmatter of a page.
"""
function frontmatter(page::Page) :: Dict{String, Any}
    frontmatter, _ = readpage(page)
    result = YAML.load(frontmatter)
    if result === nothing
        return Dict()
    end
    result
end

function pagecontent(page::Page) :: String
    _, content = readpage(page)
    return content
end

function markdown(page::Page) :: Markdown.MD
    Markdown.parse(pagecontent(page))
end

end