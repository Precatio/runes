/**
 * Exporterar HTML-innehåll till ett Google Docs-dokument.
 */
export async function exportToGoogleDocs(htmlContent: string, title: string, accessToken: string): Promise<string> {
  const boundary = "-------314159265358979323846";
  const delimiter = `\r\n--${boundary}\r\n`;
  const close_delim = `\r\n--${boundary}--`;
  
  const metadata = {
    name: title,
    mimeType: "application/vnd.google-apps.document" // Detta tvingar konvertering till Google Docs
  };

  const multipartRequestBody =
    delimiter +
    "Content-Type: application/json\r\n\r\n" +
    JSON.stringify(metadata) +
    delimiter +
    "Content-Type: text/html\r\n\r\n" +
    htmlContent +
    close_delim;

  const response = await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${accessToken}`,
      "Content-Type": `multipart/related; boundary=${boundary}`,
    },
    body: multipartRequestBody
  });

  if (!response.ok) {
    throw new Error(`Kunde inte ladda upp till Google Drive: ${response.statusText}`);
  }

  const data = await response.json();
  
  // Return the webViewLink if available, otherwise construct standard docs URL
  return `https://docs.google.com/document/d/${data.id}/edit`;
}
