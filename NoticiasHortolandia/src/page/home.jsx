import Card from "../components/Card.jsx";
import Artigo from "../components/Artigo.jsx";

function Home() {
  return (
    <div className="home">
      <div className="home-header">
        <h1 className="text-center mt-10 font-bold">HotolândiaNews!</h1>
        <p className="text-center">Notícias em tempo real sobre esportes, tecnologia e negócios em Hotolândia.</p>
      </div>

      <div className="home-content flex flex-wrap justify-center mt-10 gap-4">
        <Card
          title="Esportes"
          imgSrc="https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=600&q=80"
          text="Marilson é a esperança brasileira na maratona do Mundial de Berlim"
          link="https://ge.globo.com/Esportes/Noticias/Atletismo/0,,MUL1276165-16316,00.html"
        />
        <Card
          imgSrc="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80"
          title="Tecnologia"
          text="Inteligência artificial e inovação aceleram a transformação digital no Brasil."
          link="https://www.techtudo.com.br/"
        />
        <Card
          imgSrc="https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=600&q=80"
          title="Negócios"
          text="Empreendedores apostam em soluções criativas para crescer em mercados competitivos."
          link="https://www.sebrae.com.br/sites/PortalSebrae"
        />
      </div>

      <div className="mt-10 px-4">
        <h2 className="ml-7 text-2xl font-bold mb-4 text-gray-900">Casos de Polícia</h2>
        <div className="flex flex-wrap justify-center gap-4">
          <Card
            imgSrc="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRbrdvL7s4dSrHvVdAoY77SYsuxR5ftcFwijy60UBCTbxHA4ygiOl-ij7E&s=10"
            title="Homem é preso suspeito de matar a mulher a facadas em Hortolândia"
            text="Um homem foi preso suspeito de matar a mulher a facadas em Hortolândia, São Paulo. O crime ocorreu na noite de quarta-feira (3) e a vítima foi encontrada sem vida em sua residência. A polícia investiga o caso e busca entender as motivações do crime."
            link="https://g1.globo.com/sp/campinas-regiao/noticia/2026/09/04/homem-e-preso-suspeito-de-matar-a-mulher-a-facadas-em-hortolandia.ghtml"
          />
          <Card
            imgSrc="https://s2-g1.glbimg.com/HnmKSw3ceWIHpJb4VxHIKO9cz7s=/1383x0/filters:format(jpeg)/https://i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2026/0/6/MrTCFDTS6f66R1G57Ddg/jovem-araraquara.jpg"
            title="Polícia investiga morte de jovem em acidente de trânsito em Campinas"
            text="A polícia investiga a morte de um jovem em um acidente de trânsito em Campinas, São Paulo. O acidente ocorreu na madrugada de sábado (6) e envolveu dois veículos. A vítima foi socorrida, mas não resistiu aos ferimentos. As autoridades estão apurando as circunstâncias do acidente."
            link="https://g1.globo.com/sp/campinas-regiao/noticia/2026/09/07/policia-investiga-morte-de-jovem-em-acidente-de-transito-em-campinas.ghtml"
          />
          <Card
            imgSrc="https://s2-g1.glbimg.com/0J3g5k6F7z8G9Z4x5K8H9J7c8sE=/1383x0/filters:format(jpeg)/https://i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2026/0/7/8Y6F7G9H8J9K0L1M2N3O/policia-investiga-assassinato-em-sao-paulo.jpg"
            title="Polícia investiga assassinato em São Paulo"
            text="A polícia investiga um assassinato ocorrido em São Paulo. A vítima foi encontrada sem vida em um beco na região central da cidade. As autoridades estão coletando evidências e buscando testemunhas para esclarecer o caso."
            link="https://g1.globo.com/sp/sao-paulo/noticia/2026/09/08/policia-investiga-assassinato-em-sao-paulo.ghtml"
          />
        </div>
      </div>

      
    </div>
  );
}

export default Home;