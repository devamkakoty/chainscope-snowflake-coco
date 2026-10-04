param(
    [string]$Template = 'D:\MoneyMaker\data\operations\snowflake-hackathon-template-20261004\prototype-submission-template.pptx',
    [string]$OutputPptx = 'D:\MoneyMaker\services\snowflake-supply-chain-copilot\artifacts\ChainScope-CoCo-Hackathon-Deck.pptx',
    [string]$OutputPdf = 'D:\MoneyMaker\services\snowflake-supply-chain-copilot\artifacts\ChainScope-CoCo-Hackathon-Deck.pdf'
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$artifacts = (Resolve-Path -LiteralPath (Join-Path $project 'artifacts')).Path
foreach ($path in @($OutputPptx, $OutputPdf)) {
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetDirectoryName($path))
    if ($parent -cne $artifacts) { throw "Output must stay in $artifacts" }
}
if (-not (Test-Path -LiteralPath $Template)) { throw 'Official template missing.' }

$pp = New-Object -ComObject PowerPoint.Application
$pp.Visible = -1
$deck = $null
try {
    $deck = $pp.Presentations.Open($Template, $false, $false, $false)
    while ($deck.Slides.Count -lt 6) {
        [void]$deck.Slides.Add($deck.Slides.Count + 1, 12)
    }
    while ($deck.Slides.Count -gt 6) {
        $deck.Slides.Item($deck.Slides.Count).Delete()
    }
    # Normalize the organizer template to widescreen before placing content.
    $deck.PageSetup.SlideWidth = 960
    $deck.PageSetup.SlideHeight = 540
    $W = $deck.PageSetup.SlideWidth
    $H = $deck.PageSetup.SlideHeight
    $bg = 0x1A1714
    $green = 0x6A9E16
    $light = 0xF6F4EF
    $muted = 0xC9C3B8
    $white = 0xFFFFFF

    function Clear-Slide($slide) {
        for ($i = $slide.Shapes.Count; $i -ge 1; $i--) { $slide.Shapes.Item($i).Delete() }
        $slide.FollowMasterBackground = 0
        $slide.Background.Fill.ForeColor.RGB = $script:bg
        $slide.Background.Fill.Solid()
    }
    function Add-Text($slide, $text, $x, $y, $w, $h, $size, $color, $bold = $false) {
        $shape = $slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
        $shape.TextFrame.TextRange.Text = $text
        $shape.TextFrame.TextRange.Font.Name = 'Aptos'
        $shape.TextFrame.TextRange.Font.Size = $size
        $shape.TextFrame.TextRange.Font.Color.RGB = $color
        $shape.TextFrame.TextRange.Font.Bold = if ($bold) { -1 } else { 0 }
        $shape.TextFrame.MarginLeft = 0
        $shape.TextFrame.MarginRight = 0
        $shape.TextFrame.MarginTop = 0
        $shape.TextFrame.MarginBottom = 0
        return $shape
    }
    function Add-Header($slide, $kicker, $title, $subtitle) {
        [void](Add-Text $slide $kicker 38 22 820 22 11 $script:green $true)
        [void](Add-Text $slide $title 38 48 820 58 28 $script:white $true)
        [void](Add-Text $slide $subtitle 38 108 820 35 12 $script:muted $false)
        $line = $slide.Shapes.AddShape(1, 38, 145, 74, 3)
        $line.Fill.ForeColor.RGB = $script:green
        $line.Line.Visible = 0
    }
    function Add-PictureFit($slide, $path, $x, $y, $w, $h) {
        $pic = $slide.Shapes.AddPicture($path, 0, -1, $x, $y, -1, -1)
        $scale = [Math]::Min($w / $pic.Width, $h / $pic.Height)
        $pic.Width *= $scale
        $pic.Height *= $scale
        $pic.Left = $x + (($w - $pic.Width) / 2)
        $pic.Top = $y + (($h - $pic.Height) / 2)
        return $pic
    }
    function Add-Card($slide, $x, $y, $w, $h, $title, $body) {
        $card = $slide.Shapes.AddShape(5, $x, $y, $w, $h)
        $card.Fill.ForeColor.RGB = 0x2A2723
        $card.Line.ForeColor.RGB = 0x45413B
        [void](Add-Text $slide $title ($x+15) ($y+14) ($w-30) 28 15 $script:white $true)
        [void](Add-Text $slide $body ($x+15) ($y+50) ($w-30) ($h-58) 11 $script:muted $false)
    }

    $shots = Join-Path $artifacts 'screenshots'

    $s = $deck.Slides.Item(1); Clear-Slide $s
    [void](Add-Text $s 'CHAINSCOPE' 48 70 820 35 15 $green $true)
    [void](Add-Text $s 'Supply-chain answers you can trace to the source.' 48 124 790 120 34 $white $true)
    [void](Add-Text $s 'Governed conversational analytics for Snowflake CoCo CLI Hackathon - Problem Statement 05' 48 265 760 60 17 $muted $false)
    [void](Add-Text $s 'Devam Kakoty  |  Team size: 1  |  Bengaluru, India' 48 425 760 32 13 $light $true)
    [void](Add-Text $s 'Synthetic demonstration data  |  Public repository and live replay included' 48 465 760 25 11 $muted $false)

    $s = $deck.Slides.Item(2); Clear-Slide $s
    Add-Header $s '01  PROBLEM BRIEF' 'A late shipment is not yet an explanation.' 'Operations teams need the affected commitment, approved metric and evidence in one governed answer.'
    Add-Card $s 38 180 270 250 'Pain today' "Supplier, inventory and customer-risk signals live in separate views.`n`nFree-form assistants can mix definitions, invent joins or disclose commercial values."
    Add-Card $s 326 180 270 250 'Target users' "Supply planners`nProcurement teams`nPlant operations`nCommercial analysts`nGovernance and audit teams"
    Add-Card $s 614 180 270 250 'Result' "Trace an inbound problem to specific open demand.`n`nReturn deterministic metrics, approved SQL and exact source records - or refuse the question."

    $s = $deck.Slides.Item(3); Clear-Slide $s
    Add-Header $s '02  WORKING PROTOTYPE' 'Ask -> govern -> calculate -> cite.' 'Seven business questions are mapped to explicit metric contracts and source evidence.'
    [void](Add-PictureFit $s (Join-Path $shots '02-governed-answer.png') 35 165 560 330)
    Add-Card $s 620 168 270 320 'Live path' "1. User selects an approved question`n`n2. Role and field policy are checked before execution`n`n3. Shared SQL metric runs at a defined grain`n`n4. Result returns source IDs and records`n`n5. Decision is written to the session audit trail"

    $s = $deck.Slides.Item(4); Clear-Slide $s
    Add-Header $s '03  ARCHITECTURE' 'One ontology, shared metric contracts.' 'The local app proves behavior; Snowflake assets define the account deployment path.'
    [void](Add-PictureFit $s (Join-Path $shots '04-supply-network.png') 35 165 525 325)
    Add-Card $s 585 165 305 92 'Data layer' 'Suppliers -> parts -> plants -> shipments -> order lines -> customers'
    Add-Card $s 585 272 305 92 'Governance layer' 'Question allowlist, role checks, redaction, source citations, audit chain'
    Add-Card $s 585 379 305 112 'Snowflake path' 'Load SQL, shared views, native Semantic Views, object grants, Cortex Analyst request and CoCo review prompts'

    $s = $deck.Slides.Item(5); Clear-Slide $s
    Add-Header $s '04  GOVERNANCE BY DESIGN' 'The right answer for the right role.' 'Commercial exposure is calculated from at-risk lines and denied before query for operations users.'
    [void](Add-PictureFit $s (Join-Path $shots '03-commercial-exposure.png') 35 165 510 300)
    [void](Add-PictureFit $s (Join-Path $shots '05-audit-trail.png') 565 165 330 300)
    [void](Add-Text $s 'Operations: denied  |  Commercial: USD 67,050 gross open-order exposure  |  Unsupported predictions: refused' 38 480 850 36 13 $light $true)

    $s = $deck.Slides.Item(6); Clear-Slide $s
    Add-Header $s '05  IMPACT & EVIDENCE' 'Built to be inspected, extended and deployed.' 'Every figure below is from the reproducible synthetic snapshot - not a claimed client outcome.'
    Add-Card $s 38 170 200 115 '56 tests passed' 'Metrics, integrity, API, security and static replay.'
    Add-Card $s 255 170 200 115 '58 browser checks' '29 local + 29 static; desktop and mobile.'
    Add-Card $s 472 170 200 115 '7 governed metrics' 'Late supply, risk, inventory, fill, sourcing and exposure.'
    Add-Card $s 689 170 200 115 '163 records' '11 tables, 32 shipments, 14 orders.'
    Add-Card $s 38 310 410 155 'Measured demo outputs' "5 overdue inbound shipments`n4 at-risk customer orders`n55.2% supplier on-time delivery`n41.6% unit fill"
    Add-Card $s 472 310 417 155 'Reusable path' "Static public replay + local app + CLI`nSnowflake Semantic Views and least-privilege grants`nDeterministic synthetic-data generator`nGitHub-ready source and documentation"
    [void](Add-Text $s 'Repository: github.com/devamkakoty/chainscope-snowflake-coco  |  Demo: devamkakoty.github.io/chainscope-snowflake-coco/' 38 495 850 25 10 $muted $false)

    if (Test-Path -LiteralPath $OutputPptx) { Remove-Item -LiteralPath $OutputPptx -Force }
    if (Test-Path -LiteralPath $OutputPdf) { Remove-Item -LiteralPath $OutputPdf -Force }
    $deck.SaveAs($OutputPptx, 24)
    $deck.SaveAs($OutputPdf, 32)
} finally {
    if ($null -ne $deck) { $deck.Close() }
    $pp.Quit()
    [Runtime.InteropServices.Marshal]::FinalReleaseComObject($pp) | Out-Null
}

$files = foreach ($path in @($OutputPptx, $OutputPdf)) {
    $item = Get-Item -LiteralPath $path
    [ordered]@{
        path = $item.FullName
        bytes = $item.Length
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    }
}
$files | ConvertTo-Json -Depth 3
