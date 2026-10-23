function Card({ imgSrc, title, text, link }) {
    const image = imgSrc || 'https://via.placeholder.com/300x180?text=Imagem';

    return (
        <div className="card bg-white shadow-md rounded-lg p-4 m-4 w-72 flex-shrink-0">
            <a href={link} target="_blank" rel="noopener noreferrer" className="block">
                <h2 className="card-title text-lg text-gray-800 text-center font-bold">{title}</h2>
                <img src={image} alt={title} className="w-full h-40 object-cover rounded-md mt-3" />
                <p className="card-text text-gray-700 mt-2">{text}</p>
            </a>
        </div>
    );
}

export default Card;