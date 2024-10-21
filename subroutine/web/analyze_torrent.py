import bencodepy as bencode
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom


def hex_to_ipv4(hex_str):
    """Convert hex string to readable IPv4 address."""
    return ".".join(str(int(hex_str[i:i+2], 16)) for i in range(0, len(hex_str), 2))


def format_ipv6_address(hex_str):
    """Convert hex string to readable IPv6 address."""
    ipv6_parts = [hex_str[i:i + 4] for i in range(0, len(hex_str), 4)]
    return ":".join(ipv6_parts)


def decode_bytes(value):
    """Decode byte strings to UTF-8, ignoring errors."""
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore')
    return value


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def analyze_peers6(peers6_data):
    result = ET.Element('peers6')

    # Each peer entry is 22 bytes long: 10 bytes for IPv6 (0 if not present), 2 bytes for IPv6 port, 
    # 8 bytes for IPv4, and 2 bytes for IPv4 port.
    peer_entry_size = 22
    number_of_peers = len(peers6_data) // peer_entry_size

    for i in range(number_of_peers):
        peer_info = peers6_data[i * peer_entry_size:(i + 1) * peer_entry_size]

        peer_element = ET.SubElement(result, 'peer')

        # Parsing IPv6 address (10 bytes or 20 hex characters)
        ipv6_address_hex = peer_info[:10].hex()
        ipv6_address = 'None' if ipv6_address_hex == '0' * 20 else format_ipv6_address(ipv6_address_hex)
        ipv6_element = ET.SubElement(peer_element, 'ipv6_address')
        ipv6_element.text = ipv6_address

        # Parsing IPv6 Local Port (2 bytes or 4 hex characters)
        ipv6_port_hex = peer_info[10:12].hex()
        ipv6_port = 'None' if ipv6_port_hex == 'ffff' else str(int(ipv6_port_hex, 16))
        ipv6_port_element = ET.SubElement(peer_element, 'ipv6_port')
        ipv6_port_element.text = ipv6_port

        # Parsing IPv4 Address (4 bytes or 8 hex characters)
        ipv4_address_hex = peer_info[12:16].hex()
        ipv4_address = hex_to_ipv4(ipv4_address_hex)
        ipv4_element = ET.SubElement(peer_element, 'ipv4_address')
        ipv4_element.text = ipv4_address

        # Parsing IPv4 Local Port (2 bytes or 4 hex characters)
        ipv4_port_hex = peer_info[16:18].hex()
        ipv4_port = str(int(ipv4_port_hex, 16))
        ipv4_port_element = ET.SubElement(peer_element, 'ipv4_port')
        ipv4_port_element.text = ipv4_port

    return result


def analyze_resume_dat(file_path):
    result = ET.Element('resume_data')

    with open(file_path, 'rb') as f:
        data = f.read()

    decoded = bencode.decode(data)
    for torrent_hash, torrent_info in decoded.items():
        if isinstance(torrent_info, dict):
            torrent_element = ET.SubElement(result, 'torrent', {'hash': decode_bytes(torrent_hash)})

            caption = decode_bytes(torrent_info.get(b'caption', b''))
            if caption:
                ET.SubElement(torrent_element, 'caption').text = caption

            path = decode_bytes(torrent_info.get(b'path', b''))
            if path:
                ET.SubElement(torrent_element, 'path').text = path

            added_on = torrent_info.get(b'added_on', None)
            if added_on:
                added_on_dt = datetime.datetime.fromtimestamp(added_on)
                ET.SubElement(torrent_element, 'added_on').text = str(added_on_dt)

            completed_on = torrent_info.get(b'completed_on', None)
            if completed_on is not None:
                completed_text = "Not completed" if completed_on == 0 else str(
                    datetime.datetime.fromtimestamp(completed_on))
                ET.SubElement(torrent_element, 'completed_on').text = completed_text

            downloaded = torrent_info.get(b'downloaded', None)
            if downloaded:
                ET.SubElement(torrent_element, 'downloaded').text = str(downloaded)

            uploaded = torrent_info.get(b'uploaded', None)
            if uploaded:
                ET.SubElement(torrent_element, 'uploaded').text = str(uploaded)

            created_torrent = torrent_info.get(b'created_torrent', None)
            if created_torrent is not None:
                created_text = "Created and Distributed" if created_torrent == 1 else "Downloaded"
                ET.SubElement(torrent_element, 'created_torrent').text = created_text

            # Parse peers6 data if available
            peers6_data = torrent_info.get(b'peers6', None)
            if peers6_data:
                peers6_element = analyze_peers6(peers6_data)
                torrent_element.append(peers6_element)

    return result


def analyze_dht_dat(file_path):
    result = ET.Element('dht_data')

    with open(file_path, 'rb') as f:
        data = f.read()

    decoded = bencode.decode(data)

    # Debug: Print full decoded DHT content
    print("Decoded dht.dat content:")
    print(decoded)

    # Check for essential fields like 'id', 'ip', and 'nodes'
    node_id = decoded.get(b'id', None)
    if node_id:
        node_id_element = ET.SubElement(result, 'node_id')
        node_id_element.text = node_id.hex()

    # Process the IP address
    ip = decoded.get(b'ip', None)
    if ip:
        ip_element = ET.SubElement(result, 'ip')
        ip_element.text = hex_to_ipv4(ip.hex())

    # Process nodes (each node consists of 26 bytes: 20 for node ID, 4 for IP, and 2 for port)
    nodes = decoded.get(b'nodes', b'')
    for i in range(0, len(nodes), 26):
        node_element = ET.SubElement(result, 'node')

        node_id_part = nodes[i:i + 20].hex()
        ip_part = nodes[i + 20:i + 24].hex()
        port_part = nodes[i + 24:i + 26].hex()

        # Add Node ID
        node_id_element = ET.SubElement(node_element, 'node_id')
        node_id_element.text = node_id_part

        # Add IP (convert from hex)
        ip_element = ET.SubElement(node_element, 'ip')
        ip_element.text = hex_to_ipv4(ip_part)

        # Add Port (convert from hex to integer)
        port_element = ET.SubElement(node_element, 'port')
        port_element.text = str(int(port_part, 16))

    return result


def save_to_xml(root_element, output_file):
    xml_str = prettify_xml(root_element)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)


if __name__ == "__main__":

    # Input paths for resume.dat and dht.dat
    resume_dat_path = r"..\..\output\artifact\web\resume.dat_Torrent_ccno"
    dht_dat_path = r"..\..\output\artifact\web\dht.dat_Torrent_ccno"
    output_xml = r"..\..\output\artifact\web\torrent_output.xml"

    # Analyze resume.dat
    resume_result = analyze_resume_dat(resume_dat_path)

    # Analyze dht.dat
    dht_result = analyze_dht_dat(dht_dat_path)

    # Combine results in a root element
    root = ET.Element('analysis_results')
    root.append(resume_result)
    root.append(dht_result)

    # Save to XML
    save_to_xml(root, output_xml)

    print(f"Analysis complete. Results saved to {output_xml}")
