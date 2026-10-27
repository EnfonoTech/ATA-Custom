// The client folder's two subfolders are named from the client's side:
//   Incoming  what ATA sends to the client
//   Outgoing  what the client sends to ATA
// ATA staff read them the other way round (what they send out is "Outgoing"), so staff
// screens swap the two words. Display only: the real folder names, the File records
// and every path sent to the server stay as they are.
const CLIENT_SUB_RE = /(^|\/)(06[\s-]*CLIENT SUBMITTAL)\/(Incoming|Outgoing)(?=\/|$)/i;

const SWAP = { incoming: "Outgoing", outgoing: "Incoming" };

/** A folder path (or label) as this viewer should read it. */
export function viewerFolderPath(path, isClient) {
	const text = String(path || "");
	if (isClient) return text;
	return text.replace(CLIENT_SUB_RE, (_, lead, root, sub) => `${lead}${root}/${SWAP[sub.toLowerCase()]}`);
}

/** The last segment of a folder path, as this viewer should read it. */
export function viewerFolderLeaf(path, isClient) {
	const parts = viewerFolderPath(path, isClient).split("/");
	return parts[parts.length - 1] || "";
}
