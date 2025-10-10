import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from textwrap import dedent
from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["HUGGINGFACE_API_KEY"] = os.getenv("HF_TOKEN")

server_params = StdioServerParameters(
    command="python",
    args=["src/tools/mcp_tool.py"]
)
DEBUG = False

prompt_template = dedent("""
Anda adalah seorang ahli hukum Indonesia.
Gunakan bahasa Indonesia yang baik dan benar, sesuai dengan kaidah Kamus Besar Bahasa Indonesia (KBBI) dan Pedoman Umum Ejaan Bahasa Indonesia (PUEBI).
Dalam menjawab, prioritaskan penggunaan tool `peraturan_go_id_search()` untuk mendapatkan konteks dan elaborasi lebih lanjut mengenai kasus yang terjadi.
Jika informasi tidak ditemukan melalui alat tersebut, katakanlah bahwa anda tidak dapat menggunakan informasi menggunakan keyword yang anda gunakan.
Jelaskan peraturan, undang-undang, atau kebijakan yang relevan yang dilanggar, serta berikan penjelasan singkat mengenai bagaimana pelanggaran tersebut terjadi.
Jelaskan langkah-langkah hukum, administratif, atau praktis yang dapat dilakukan untuk menyelesaikan atau menangani kasus tersebut.  
Jelaskan jenis hukuman atau sanksi yang mungkin diterima oleh pihak yang melanggar, baik dalam bentuk pidana, perdata, administratif, maupun sanksi sosial, sesuai dengan regulasi yang berlaku.
Apabila dalam kasus terdapat nominal uang atau transaksi keuangan, harap selalu cantumkan dalam mata uang Rupiah Indonesia (IDR), dan apabila perlu, sertakan juga konversi atau rincian asal nominal tersebut.
Susun jawaban secara sistematis dan gunakan penanda yang jelas untuk setiap bagian. Berikan analisis secara objektif, tanpa memasukkan opini pribadi atau penilaian moral.
Jika ada informasi yang belum tersedia atau masih meragukan, nyatakan dengan tegas bahwa informasi tersebut perlu divalidasi lebih lanjut.

Querynya adalah:

{query}
""")


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)
            model = init_chat_model(
                "openai:gpt-4.1",
                temperature=0,
            )
            agent = create_react_agent(
                model=model,
                tools=tools,
            )

            while True:
                try:
                    query = input("User > ")
                    if not query:
                        continue

                    response = await agent.ainvoke({
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt_template.format(query=query)
                            }
                        ]
                    })
                    response = response["messages"]
                    for resp in response:      
                        if "tool_call_id" in dir(resp) and DEBUG:
                            print("!!DEBUG::TOOL CALLED", resp)    
         
                    print(f"Assistant > {response[-1].content}\n")
                
                except KeyboardInterrupt:
                    print("Exiting...")
                    break
                
                except Exception as e:
                    print(f"{type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
