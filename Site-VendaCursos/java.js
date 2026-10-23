const products = [
    { id: 1, title: "Curso de HTML para Iniciantes", category: "Criatividade", price: 29.90, oldPrice: 59.90, rating: "4,9", tag: "Mais vendido", label: "DESIGN SEM COMPLICAÇÃO", cover: "#c47f5e", shape: "#e6b47a", ink: "#fff9ed", symbol: "✳", image: "img/Apostila HTML para Iniciantes.jpeg", purchaseUrl: "https://pay.kiwify.com.br/eIDLR2C" },
    { id: 2, title: "Apostila de CSS para Iniciantes", category: "Tecnologia", price: 29.90, oldPrice: 69.90, rating: "4,8", tag: "Queridinho", label: "DOMINE AS PLANILHAS", cover: "#467956", shape: "#90b977", ink: "#f7f6e9", symbol: "▦", image: "img/Apostila de css.jpeg", purchaseUrl: "https://pay.kiwify.com.br/NmHNhk7" },
    { id: 3, title: "Apostila de JavaScripts para Iniciantes", category: "Idiomas", price: 29.90, oldPrice: 49.90, rating: "5,0", tag: "Novo", label: "ENGLISH EVERY DAY", cover: "#647ba3", shape: "#a8c0d0", ink: "#f5f7f2", symbol: "Aa", image: "img/apostila de javaescript.jpeg", purchaseUrl: "https://pay.kiwify.com.br/MqPCcr4" },
    { id: 4, title: "Marketing Digital na Prática", category: "Negócios", price: 44.90, oldPrice: 64.90, rating: "4,9", tag: "Mais vendido", label: "IDEIAS QUE CONECTAM", cover: "#c18d49", shape: "#e5c479", ink: "#fff9ed", symbol: "↗", purchaseUrl: "" },
    { id: 5, title: "Gestão Financeira Pessoal", category: "Negócios", price: 29.90, oldPrice: 44.90, rating: "4,8", tag: "Essencial", label: "CUIDE DO SEU FUTURO", cover: "#527d76", shape: "#9ebca2", ink: "#f5f7ed", symbol: "R$", purchaseUrl: "" },
    { id: 6, title: "Fotografia com Celular", category: "Criatividade", price: 32.90, oldPrice: 49.90, rating: "4,9", tag: "Prático", label: "UM NOVO OLHAR", cover: "#9b687e", shape: "#d39b9e", ink: "#fff4ee", symbol: "◉", purchaseUrl: "" },
    { id: 7, title: "Lógica de Programação", category: "Tecnologia", price: 54.90, oldPrice: 79.90, rating: "4,9", tag: "Do zero", label: "PENSE COMO DEV", cover: "#5d6e55", shape: "#9baa69", ink: "#f4f5e8", symbol: "{ }", purchaseUrl: "" },
    { id: 8, title: "Espanhol para Viagens", category: "Idiomas", price: 27.90, oldPrice: 39.90, rating: "4,8", tag: "Leve com você", label: "VIAJE SIN MIEDO", cover: "#bd715c", shape: "#e6a77c", ink: "#fff4e8", symbol: "¡", purchaseUrl: "" }
];

const categories = ["Todas", ...new Set(products.map((product) => product.category))];
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const grid = document.querySelector("#catalog-grid");
const categoryList = document.querySelector("#category-list");
const searchInput = document.querySelector("#search-input");
const resultsCount = document.querySelector("#results-count");
const emptyState = document.querySelector("#empty-state");
const toast = document.querySelector("#toast");
let selectedCategory = "Todas";
let toastTimeout;

document.querySelector("#current-year").textContent = new Date().getFullYear();

function renderCategories() {
    categoryList.innerHTML = categories.map((category) => `
        <button class="category-button${category === selectedCategory ? " active" : ""}"
            type="button" aria-pressed="${category === selectedCategory}" data-category="${category}">
            ${category}
        </button>
    `).join("");
}

function renderProducts() {
    const term = searchInput.value.trim().toLocaleLowerCase("pt-BR");
    const filteredProducts = products.filter((product) => {
        const matchesCategory = selectedCategory === "Todas" || product.category === selectedCategory;
        const matchesSearch = `${product.title} ${product.category} ${product.label}`.toLocaleLowerCase("pt-BR").includes(term);
        return matchesCategory && matchesSearch;
    });

    resultsCount.textContent = `${filteredProducts.length} ${filteredProducts.length === 1 ? "apostila encontrada" : "apostilas encontradas"}`;
    emptyState.hidden = filteredProducts.length > 0;
    grid.innerHTML = filteredProducts.map((product) => `
        <article class="product-card">
            <div class="product-cover${product.image ? " has-image" : ""}" style="--cover: ${product.cover}; --cover-shape: ${product.shape}; --cover-ink: ${product.ink}; background: ${product.cover}">
                ${product.image ? `<img class="product-cover-image" src="${product.image}" alt="Capa da apostila ${product.title}">` : ""}
                <span class="cover-tag">${product.tag}</span>
                <span class="cover-symbol" aria-hidden="true">${product.symbol}</span>
                <div class="cover-copy"><small>${product.label}</small><strong>${product.title}</strong></div>
            </div>
            <div class="product-info">
                <span class="product-category">${product.category}</span>
                <h3>${product.title}</h3>
                <div class="product-rating" aria-label="${product.rating} de 5 estrelas">★★★★★ <span>${product.rating}</span></div>
                <div class="product-bottom">
                    <div class="product-price"><del>${money.format(product.oldPrice)}</del><strong>${money.format(product.price)}</strong></div>
                    <button class="buy-button" type="button" data-buy="${product.id}" aria-label="Comprar ${product.title}">Comprar <span aria-hidden="true">↗</span></button>
                </div>
            </div>
        </article>
    `).join("");
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(toastTimeout);
    toastTimeout = window.setTimeout(() => toast.classList.remove("visible"), 2600);
}

categoryList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    selectedCategory = button.dataset.category;
    renderCategories();
    renderProducts();
});

searchInput.addEventListener("input", renderProducts);

grid.addEventListener("click", (event) => {
    const button = event.target.closest("[data-buy]");
    if (!button) return;
    const product = products.find((item) => item.id === Number(button.dataset.buy));
    if (!product.purchaseUrl.trim()) {
        showToast(`O link de compra de "${product.title}" ainda será configurado.`);
        return;
    }

    let purchaseUrl;
    try {
        purchaseUrl = new URL(product.purchaseUrl);
    } catch {
        showToast("O link desta apostila não é válido. Confira o endereço configurado.");
        return;
    }
    if (!["http:", "https:"].includes(purchaseUrl.protocol)) {
        showToast(" http://https://pay.kiwify.com.br/eIDLR2C");
        return;
    }
    window.location.assign(purchaseUrl.href);
});

document.querySelector("#newsletter-form").addEventListener("submit", (event) => {
    event.preventDefault();
    document.querySelector("#newsletter-message").textContent = "Inscrição registrada! Obrigado por se juntar à Estudaí.";
    event.currentTarget.reset();
});

renderCategories();
renderProducts();
