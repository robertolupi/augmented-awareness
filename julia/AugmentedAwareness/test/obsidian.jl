using AugmentedAwareness.Obsidian

using Dates
using Test
using Markdown

@testset "obsidian.jl" begin
    @testset "Vault" begin
        vault = Vault("../../../test_vault")
        @test isdir(vault.path)
    end

    @testset "pages" begin
        vault = Vault("../../../test_vault")
        pages = AugmentedAwareness.Obsidian.pages(vault)
        @test length(pages) == 3
        @test haskey(pages, "index")
        @test haskey(pages, "2025-03-30")
        @test haskey(pages, "2025-04-01")
    end

    @testset "page" begin
        vault = Vault("../../../test_vault")
        pages = AugmentedAwareness.Obsidian.pages(vault)
        @test AugmentedAwareness.Obsidian.frontmatter(pages["2025-04-01"]) == Dict("stress" => 5)
        @test AugmentedAwareness.Obsidian.frontmatter(pages["index"]) == Dict()
        @test !occursin("stress", AugmentedAwareness.Obsidian.pagecontent(pages["2025-04-01"])) 
        @test AugmentedAwareness.Obsidian.markdown(pages["index"]) isa Markdown.MD

        Event = AugmentedAwareness.Obsidian.Event
        @test AugmentedAwareness.Obsidian.events(pages["2025-04-01"]) == [
            Event(Date(2025, 4, 1), Time(6,4), Time(7,0), "woke up"),
            Event(Date(2025, 4, 1), Time(7,0), Time(8,30), "#aww did some personal development"),
            Event(Date(2025, 4, 1), Time(8,30), Time(9,30), "#work"),
        ]
    end
end
