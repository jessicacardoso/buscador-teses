from typing import Callable

import streamlit as st

from src.web.mypages.homepage import page as homepage
from src.web.mypages.rag.qa import main as rag_main


def create_button(
    text: str,
    name: str,
    current_page: str,
    change_page_func: Callable[[str], None],
) -> st.sidebar.button:
    """Cria um botão na sidebar.

    Args:
        text (str): Texto do botão.
        name (str): Nome da página associada ao botão.
        current_page (str): Página atual.
        change_page_func (Callable[[str], None]): Função para alterar a página.

    Returns:
        st.sidebar.button: Botão criado.
    """
    return st.sidebar.button(
        text,
        use_container_width=True,
        on_click=change_page_func,
        args=(name,),
        type="primary" if current_page == name else "secondary",
    )


def change_page(name: str) -> None:
    """Altera a página atual."""
    st.session_state["page"] = name


def main():
    # Configurações da página
    st.set_page_config(
        page_title="Teses e Dissertações - Buscador",
        page_icon=":books:",
        layout="wide",
    )

    with open("src/web/static/style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.sidebar.markdown(
        """
        <a href="https://dadosabertos.capes.gov.br/" target="_blank">
        <img src="https://dadosabertos.capes.gov.br/img/caixa.png" class="sidebar_logo">
        </a>
        <h1 class="sidebar_title"> Teses e Dissertações - <span class="highlighted">Buscador</span></h1>
        <p class="sidebar_subtitle">Busca de teses e dissertações entre 2013 e 2022</p>
        """,  # noqa
        unsafe_allow_html=True,
    )

    # Mapeamento de páginas disponíveis
    pages = {
        "home": homepage,
        "rag": rag_main,
    }

    # Inicialização da página atual
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    # Criação dos botões da sidebar
    current_page = st.session_state["page"]
    create_button("🏠 Página Inicial", "home", current_page, change_page)
    create_button("📚 Consultar trabalhos", "rag", current_page, change_page)
    st.sidebar.markdown(
        "<h3 class='submenu'> 📫 Contato</h3>", unsafe_allow_html=True
    )
    st.sidebar.markdown(
        """
        [![LinkedIn](https://img.shields.io/badge/LinkedIn-%230077B5?logo=linkedin&color=%230077B5)](https://www.linkedin.com/in/acissej/)
        [![Github](https://img.shields.io/badge/Github-black?logo=github)](https://github.com/jessicacardoso)
        [![DEV.to](https://img.shields.io/badge/DEV.to-black?logo=dev.to)](https://dev.to/jessicacardoso)
        [![Discord](https://img.shields.io/badge/Discord-%237289da?logo=discord&logoColor=white&labelColor=%237289da)](https://discord.com/users/601214907400060937)
        [![Telegram](https://img.shields.io/badge/Telegram-%232CA5E0?logo=telegram&logoColor=white&labelColor=%232CA5E0)](https://t.me/pal_oma)
        [![Gmail](https://img.shields.io/badge/Gmail-%23D14836?logo=gmail&logoColor=white&labelColor=%23D14836)](mailto:jcardoso@inf.puc-rio.br)
        """
    )

    # Renderização da página atual
    pages[current_page]()


if __name__ == "__main__":
    main()
