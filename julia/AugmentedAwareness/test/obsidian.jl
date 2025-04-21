using AugmentedAwareness.Obsidian
using Test

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
    end
end
