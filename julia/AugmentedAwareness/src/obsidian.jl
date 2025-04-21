module Obsidian

using Markdown
using YAML
using Dates

export Vault, Page, pages, frontmatter, pagecontent, markdown

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

"""
pagecontent(page::Page) :: String

    Extract and return the content (body) of a page.

    This function reads the content of the given `Page` object and returns the body of the markdown file, 
    excluding the frontmatter if it exists.
"""
function pagecontent(page::Page) :: String
    _, content = readpage(page)
    return content
end

"""
markdown(page::Page) :: Markdown.MD

    Parse and return the markdown content of a page as a `Markdown.MD` object.

    This function reads the body content of the given `Page` object and parses it into a `Markdown.MD` object 
    which will show a preview of the page when printed (e.g. in REPL).
"""
function markdown(page::Page) :: Markdown.MD
    Markdown.parse(pagecontent(page))
end

struct Event
    date::Date
    time_start::Time
    time_end
    name::String
end

"""
events(page::Page) :: Vector{Event}

    Extract and return a vector of events from a page.

    This function reads the content of the given `Page` object and extracts events based on the specified format.
    Each event is represented as an `Event` object containing the date, start time, end time, and name of the event.

    Beware: this function doesn't fully check the markdown syntax (e.g. it doesn't check if events-like text is present in code blocks).
    It assumes that the events are formatted in a specific way (e.g. "HH:MM - HH:MM Event Name" or ""HH:MM Event Name").
"""
function events(page::Page) :: Vector{Event}
    datestr, _ = splitext(basename(page.path))
    date = Date(datestr, dateformat"yyyy-mm-dd")
    events = Vector{Event}()
    time_starts = Vector{Time}()
    time_ends = Vector()
    names = Vector{String}()
    for line in split(pagecontent(page), "\n")
        m = match(r"^(\d{1,2}:\d{2})(?:\s*-\s*(\d{1,2}:\d{2}))?\s*(.*)$", line)
        if m !== nothing
            time_starts = push!(time_starts, Time(m.captures[1]))
            time_ends = push!(time_ends, m.captures[2] === nothing ? nothing : Time(m.captures[2]))
            names = push!(names, m.captures[3])
        end
    end
    for i in 1:length(time_starts)-1
        if time_ends[i] === nothing
            time_ends[i] = time_starts[i+1]
        end
    end
    for i in eachindex(time_starts)
        push!(events, Event(date, time_starts[i], time_ends[i], names[i]))
    end
    events
end


end