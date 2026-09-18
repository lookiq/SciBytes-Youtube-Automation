const fs = require('fs');
const path = 'C:\\Users\\MD JEWEL RANA\\.gemini\\antigravity\\brain\\e0c94447-6b13-47af-860c-4af50ce93ef6\\.system_generated\\steps\\496\\content.md';
const html = fs.readFileSync(path, 'utf8');

const titleMatch = html.match(/<title>(.*?)<\/title>/);
console.log('Page Title:', titleMatch ? titleMatch[1] : 'N/A');

const match = html.match(/var ytInitialData = (\{.*?\});<\/script>/);
if (match) {
  const str = match[1];
  const metadata = str.match(/"metadata":\{"channelMetadataRenderer":(\{.*?\}\}\})/);
  if (metadata) {
    const meta = JSON.parse(metadata[1]);
    console.log('Title:', meta.title);
    console.log('Description:\n', meta.description);
    console.log('Avatar URL:', meta.avatar?.thumbnails?.[0]?.url);
    console.log('Vanity URL:', meta.vanityChannelUrl);
    console.log('Channel ID:', meta.externalId);
  }
}
