scan_xml_schema = """\
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:copy="http://www.hp.com/schemas/imaging/con/copy/2008/07/07" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:dd3="http://www.hp.com/schemas/imaging/con/dictionaries/2009/04/06" xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05" xmlns:scc="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
	<pwg:Version>2.1</pwg:Version>
	<scan:Intent>Photo</scan:Intent>
	<pwg:ScanRegions>
		<pwg:ScanRegion>
			<pwg:Height>{height}</pwg:Height>
			<pwg:Width>{width}</pwg:Width>
			<pwg:XOffset>0</pwg:XOffset>
			<pwg:YOffset>0</pwg:YOffset>
		</pwg:ScanRegion>
	</pwg:ScanRegions>
	<pwg:InputSource>Platen</pwg:InputSource>
	<scan:DocumentFormatExt>{format}</scan:DocumentFormatExt>
	<scan:XResolution>{xdpi}</scan:XResolution>
	<scan:YResolution>{ydpi}</scan:YResolution>
	<scan:ColorMode>{colormode}</scan:ColorMode>
	<scan:CompressionFactor>0</scan:CompressionFactor>
	<scan:Brightness>1000</scan:Brightness>
	<scan:Contrast>1000</scan:Contrast>
</scan:ScanSettings>
"""