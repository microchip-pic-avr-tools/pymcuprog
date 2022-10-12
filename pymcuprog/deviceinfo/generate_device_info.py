"""
DFP harvester
"""
import os
import tempfile
from string import Template
from zipfile import ZipFile
from requests import get
import harvest

# Constants used by various servers and artifacts
MICROCHIP_ARTIFACTORY_SERVER_URL = "https://artifacts.microchip.com/artifactory"
REPO = "ivy-local"
ORG = "microchip"
REMOTE = "&remote=1"

DEVICE_INFO_TEMPLATE = '''
"""
Required device info for the $device_name devices
The following data was collected from device pack $pack_info
"""

from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
$device_data
}
'''

def fetch_latest_device_atpack(module, res_dir_path, org=ORG, repo=REPO, remote=REMOTE):
    """
    Returns path to a temporary folder containing the requested device pack (.atpack format).

    :param module: module name (DFP name) to retrieve
    :param res_dir_path: Directory to store the retrieved device pack.
    :param org: ivy organisation
    :param repo: ivy repo
    :param remote: ivy remote
    """
    search_url = "/api/search/latestVersion?g={0:s}&a={1:s}&repos={2:s}{3:s}".format(org, module, repo, remote)
    version = get(MICROCHIP_ARTIFACTORY_SERVER_URL + search_url).text
    target_file = module + "-" + version + ".atpack"
    artifact_url = "/{0:s}/{1:s}/{2:s}/{3:s}/{4:s}".format(repo, org, module, version, target_file)
    artifact = get(MICROCHIP_ARTIFACTORY_SERVER_URL + artifact_url)
    if artifact.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(prefix="{}_".format(module), suffix=".atpack", delete=False,
                                                dir=res_dir_path)
        temp_file.write(artifact.content)
        temp_file.close()
        with ZipFile(temp_file.name, "r") as zipobj:
            zipobj.extractall(res_dir_path)
        return "{} {}".format(module, version)
    return None

def extract_device_name(device_atdf_path):
    harvest_data = harvest.harvest_from_file(device_atdf_path)
    name_container_ind = harvest_data.find("'name'") + len("'name'")
    name_start_ind = harvest_data[name_container_ind:].find("'") + name_container_ind + 1
    name_end_ind = harvest_data[name_start_ind:].find("'") + name_start_ind
    name = harvest_data[name_start_ind:name_end_ind]
    return name


def add_new_updi_device(device_atdf_path, device_pack_source_str):
    """
    Add a new UPDI device

    :param device_atdf_path: Path to .atdf file of the device you wish to add
    :param device_pack_source_str: Reference string to the source of the DFP from which the .atdf file was extracted
    """
    harvest_data = harvest.harvest_from_file(device_atdf_path)
    if not "'interface': 'UPDI'" in harvest_data:
        return
    device_name = extract_device_name(device_atdf_path)
    new_device_template = Template(DEVICE_INFO_TEMPLATE)
    new_device_script = new_device_template.substitute(device_name=device_name, device_data=harvest_data,
                                                       pack_info=device_pack_source_str)

    f = open(os.getcwd().replace("\\", "/")+"/devices/" + device_name + ".py", "w")
    f.write(new_device_script)
    f.close()

def update_updi_devices():
    """
    Update all UPDI devices
    """
    packs = []
    PACKS_OF_INTEREST = ['Microchip.ATmega_DFP', 'Microchip.ATtiny_DFP', 'Microchip.AVR-']
    # Search entire path
    from artifactory import ArtifactoryPath
    path = ArtifactoryPath("{}/{}/{}".format(MICROCHIP_ARTIFACTORY_SERVER_URL, REPO, ORG))
    for a in path:
        name = str(a)
        packname = name.split('/')[-1]
        # Filter:
        if name.endswith("_DFP") and not name.endswith("ENG_DFP") and not name.endswith("DEV_DFP") and packname.startswith(tuple(PACKS_OF_INTEREST)):
            packs.append(packname)

    for pack in packs:
        print("Fetching latest pack for: {}".format(pack))
        temp_dir = tempfile.TemporaryDirectory()
        pack_info = fetch_latest_device_atpack(pack, temp_dir.name)
        devices = os.listdir(temp_dir.name.replace("\\", "/")+"/atdf")
        print("Parsing {} devices".format(len(devices)))
        for device in devices:
            add_new_updi_device(temp_dir.name.replace("\\", "/") + "/atdf/" + device, pack_info)
        print("Success.")

update_updi_devices()
