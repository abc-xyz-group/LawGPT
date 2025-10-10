import requests
from mcp.server.fastmcp import FastMCP
from io import BytesIO
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup


mcp = FastMCP("Peraturan Go Id")
BASE_URL = "https://peraturan.go.id/cari?PeraturanSearch[tentang]={search_keyword}&PeraturanSearch[nomor]=&PeraturanSearch[tahun]=&PeraturanSearch[jenis_peraturan_id]=&PeraturanSearch[pemrakarsa_id]=&PeraturanSearch[status]=Berlaku"
NUM_DOCUMENTS_LOOKUP = 3 # meaning it will only look at 3 VALID documents


@mcp.tool()
async def peraturan_go_id_search(search_keyword: str) -> str:
    """
    Get relevant content from documents regarding the given search keyword.
    Warning that it might return empty string because there are no relevant documents or
    there are no valid relevant documents.

    Args:
        search_keyword (str): relevant keywords to search for on `peraturan.go.id`.
    
    Returns:
        str: concatenated text result from reading PDFs
    """
    formatted_url = BASE_URL.format(search_keyword=search_keyword.replace(" ", "+"))
    response = requests.get(formatted_url)
    response.raise_for_status() # if not 200, then throw error

    parsed_html = BeautifulSoup(response.content, features="html.parser")
    links = parsed_html.find_all("a", href=True)
    
    num_documents_obtained = 0
    contents = []
    for link in links:
        if num_documents_obtained >= NUM_DOCUMENTS_LOOKUP:
            break

        if "/files/" not in link["href"]:
            continue

        if link["href"] == "/files/draft_kuhap.pdf":
            continue

        href = link["href"]
        pdf_url = f"https://peraturan.go.id{href}"
        try:
            # inside try-catch block because the PDF might be invalid
            pdf_response = requests.get(pdf_url)
            pdf_file_obj = BytesIO(pdf_response.content)
            reader = PdfReader(pdf_file_obj)
            content = []
            for i in range(len(reader.pages)):
                content.append(
                    reader.pages[i].extract_text()
                )

            num_documents_obtained += 1
            contents.append("\n\n".join(content))
        except:
            print(f"{pdf_url} isn't valid")
            continue # continue to next document

    return "\n\n".join(contents)


if __name__ == "__main__":
    print("Starting Peraturan Go ID Search Server")
    mcp.run(transport="stdio")
