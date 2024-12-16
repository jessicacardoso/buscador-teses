import streamlit as st


def page():
    st.markdown(
        """
        <main class="home_container">
                <h1>Buscador de Teses e Dissertações 2013-2022 </h1>
                <p> Este é um projeto inicial tem como propósito permitir a consulta sobre teses e dissertações defendidas
                entre 2013 e 2022, disponibilizados no portal de Dados Abertos da CAPES. </p>
                    Aqui, você poderá fazer consultas por palavras-chave, região, instituição, ano de defesa, entre outros.
                </p>
                <h2>Conjunto de Dados </h2>
                <p> Os dados utilizados nesse projeto são: </p>
                <ul>
                    <li> [2021 a 2024] Catálogo de Teses e Dissertações - Brasil </li>
                    <li> [2017 a 2020] Catálogo de Teses e Dissertações - Brasil </li>
                    <li> [2013 a 2016] Catálogo de Teses e Dissertações - Brasil</li>
                </ul>
                <p> Nessa demonstração dos dados estão armazenados em um bucket usando o MinIO.</p>
                <p> Na barra lateral ao lado, é possível navegar entre as páginas do projeto. As páginas disponíveis são: </p>
                <ul>
                    <li> Página Inicial: Apresentação do projeto e dos dados utilizados. </li>
                    <li> Consulta: Página para realizar consultas sobre as teses e dissertações. </li>
                </ul>
        </main>
    """,  # noqa
        unsafe_allow_html=True,
    )
