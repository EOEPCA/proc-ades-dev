$graph:
- class: Workflow
  doc: dNBR - produce the delta normalized difference between NIR and SWIR 22 over
    a pair of stac items
  id: dnbr
  inputs:
    aoi:
      doc: area of interest as a bounding box
      type: string
    bands:
      default:
      - B8A
      - B12
      - SCL
      type: string[]
    post_stac_item:
      doc: Post-event Sentinel-2 item
      type: string
    pre_stac_item:
      doc: Pre-event Sentinel-2 item
      type: string
  label: dNBR - produce the delta normalized difference between NIR and SWIR 22 over
    a pair of stac items
  outputs:
    stac:
      outputSource:
      - node_stac/stac
      type: Directory
  requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement
  - class: MultipleInputFeatureRequirement
  steps:
    node_cog:
      in:
        tif:
          source:
          - node_dnbr/dnbr
      out:
      - cog_tif
      run: '#gdal_cog_clt'
    node_dnbr:
      in:
        tifs:
          source: node_nbr/nbr
      out:
      - dnbr
      run: '#dnbr_clt'
    node_nbr:
      in:
        aoi: aoi
        stac_item:
        - pre_stac_item
        - post_stac_item
      out:
      - nbr
      run: '#nbr_wf'
      scatter: stac_item
      scatterMethod: dotproduct
    node_stac:
      in:
        post_stac_item: post_stac_item
        pre_stac_item: pre_stac_item
        tif:
          source:
          - node_cog/cog_tif
      out:
      - stac
      run: '#stacme_clt'
- class: Workflow
  doc: NBR - produce the normalized difference between NIR and SWIR 22 and convert
    to COG
  id: nbr_wf
  inputs:
    aoi:
      doc: area of interest as a bounding box
      type: string
    bands:
      default:
      - B8A
      - B12
      - SCL
      type: string[]
    stac_item:
      doc: Sentinel-2 item
      type: string
  label: NBR - produce the normalized difference between NIR and SWIR 22 and convert
    to COG
  outputs:
    nbr:
      outputSource:
      - node_cog/cog_tif
      type: File
  requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement
  steps:
    node_cog:
      in:
        tif:
          source:
          - node_nbr/nbr_tif
      out:
      - cog_tif
      run: '#gdal_cog_clt'
    node_nbr:
      in:
        stac_item: stac_item
        tifs:
          source:
          - node_subset/tifs
      out:
      - nbr_tif
      run: '#band_math_clt'
    node_stac:
      in:
        asset: bands
        stac_item: stac_item
      out:
      - asset_href
      run: '#asset_single_clt'
      scatter: asset
      scatterMethod: dotproduct
    node_subset:
      in:
        asset:
          source: node_stac/asset_href
        bbox: aoi
      out:
      - tifs
      run: '#translate_clt'
      scatter: asset
      scatterMethod: dotproduct
- arguments:
  - $( inputs.stac_item )
  baseCommand:
  - curl
  - -s
  class: CommandLineTool
  id: asset_single_clt
  inputs:
    asset:
      type: string
    stac_item:
      type: string
  outputs:
    asset_href:
      outputBinding:
        glob: message
        loadContents: true
        outputEval: '${ var assets = JSON.parse(self[0].contents).assets;

          return assets[inputs.asset].href; }'
      type: Any
  requirements:
    DockerRequirement:
      dockerPull: docker.io/curlimages/curl:latest
    InlineJavascriptRequirement: {}
    ShellCommandRequirement: {}
  stdout: message
- arguments:
  - -projwin
  - valueFrom: ${ return inputs.bbox.split(",")[0]; }
  - valueFrom: ${ return inputs.bbox.split(",")[3]; }
  - valueFrom: ${ return inputs.bbox.split(",")[2]; }
  - valueFrom: ${ return inputs.bbox.split(",")[1]; }
  - -projwin_srs
  - valueFrom: ${ return inputs.epsg; }
  - valueFrom: "${ if (inputs.asset.startsWith(\"http\")) {\n\n     return \"/vsicurl/\"\
      \ + inputs.asset; \n\n   } else { \n\n     return inputs.asset;\n\n   } \n}\n"
  - valueFrom: ${ return inputs.asset.split("/").slice(-1)[0]; }
  baseCommand: gdal_translate
  class: CommandLineTool
  id: translate_clt
  inputs:
    asset:
      type: string
    bbox:
      type: string
    epsg:
      default: EPSG:4326
      type: string
  outputs:
    tifs:
      outputBinding:
        glob: '*.tif'
      type: File
  requirements:
    DockerRequirement:
      dockerPull: docker.io/osgeo/gdal
    InlineJavascriptRequirement: {}
- arguments:
  - -out
  - valueFrom: ${ return inputs.stac_item.split("/").slice(-1)[0] + ".tif"; }
  - -exp
  - '(im3b1 == 8 or im3b1 == 9 or im3b1 == 0 or im3b1 == 1 or im3b1 == 2 or im3b1
    == 10 or im3b1 == 11) ? -2 : (im1b1 - im2b1) / (im1b1 + im2b1)'
  baseCommand: otbcli_BandMathX
  class: CommandLineTool
  id: band_math_clt
  inputs:
    stac_item:
      type: string
    tifs:
      inputBinding:
        position: 5
        prefix: -il
        separate: true
      type: File[]
  outputs:
    nbr_tif:
      outputBinding:
        glob: '*.tif'
      type: File
  requirements:
    DockerRequirement:
      dockerPull: docker.io/terradue/otb-7.2.0
    InlineJavascriptRequirement: {}
- arguments:
  - -co
  - COMPRESS=DEFLATE
  - -of
  - COG
  - valueFrom: ${ return inputs.tif }
  - valueFrom: ${ return inputs.tif.basename.replace(".tif", "") + '_cog.tif'; }
  baseCommand: gdal_translate
  class: CommandLineTool
  id: gdal_cog_clt
  inputs:
    tif:
      type: File
  outputs:
    cog_tif:
      outputBinding:
        glob: '*_cog.tif'
      type: File
  requirements:
    DockerRequirement:
      dockerPull: osgeo/gdal
    InlineJavascriptRequirement: {}
- arguments:
  - -out
  - dnbr.tif
  - -exp
  - '(im1b1 == -2 or im2b1 == -2 ) ? -20000 : (im2b1 - im1b1) * 10000'
  baseCommand: otbcli_BandMathX
  class: CommandLineTool
  id: dnbr_clt
  inputs:
    tifs:
      inputBinding:
        position: 5
        prefix: -il
        separate: true
      type: File[]
  outputs:
    dnbr:
      outputBinding:
        glob: dnbr.tif
      type: File
  requirements:
    DockerRequirement:
      dockerPull: docker.io/terradue/otb-7.2.0
    InlineJavascriptRequirement: {}
- arguments: []
  baseCommand: stacme
  class: CommandLineTool
  id: stacme_clt
  inputs:
    post_stac_item:
      inputBinding:
        position: 3
      type: string
    pre_stac_item:
      inputBinding:
        position: 2
      type: string
    tif:
      inputBinding:
        position: 1
      type: File
  outputs:
    stac:
      outputBinding:
        glob: .
      type: Directory
  requirements:
    DockerRequirement:
      dockerPull: registry.gitlab.com/app-packages/terradue/dnbr-sentinel-2-cog/stacme:0.1.0-develop
    InlineJavascriptRequirement: {}
$namespaces:
  s: https://schema.org/
cwlVersion: v1.0
s:softwareVersion: 0.1.0
schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
