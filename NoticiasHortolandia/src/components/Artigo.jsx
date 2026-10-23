function Artigo({ titulo, conteudo, imgSrc, link }) {
  return (
    <div className="artigo-container mt-10 px-4">
      <article className="artigo max-w-5xl mx-auto rounded-xl bg-white shadow-md p-6">
        <a href={link} target="_blank" rel="noopener noreferrer" className="block md:flex md:items-start md:gap-6">
          <div className="md:flex-1">
            <h1 className="artigo-titulo text-2xl font-bold mb-4 text-gray-900">{titulo}</h1>
            <p className="artigo-conteudo text-gray-700 leading-relaxed">
              {conteudo}
            </p>
          </div>

          <img
            src={imgSrc}
            alt={titulo}
            className="mt-4 md:mt-0 w-full md:w-[420px] h-72 md:h-80 object-cover rounded-lg shadow-sm"
          />
        </a>
      </article>
    </div>
  );
}

export default Artigo;