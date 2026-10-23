import { useState } from 'react';

function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  const navItems = [
    { label: 'Home', href: '/' },
    { label: 'Sobre', href: '/about' },
    { label: 'Contato', href: '/contact' },
  ];

  return (
    <header className="header bg-gray-800 text-white shadow-md">
      <div className="max-w-6xl mx-auto flex items-center justify-between p-4 relative">
        <div className="logo">
          <h1 className="text-xl font-bold">Meu Projeto</h1>
        </div>

        <button
          type="button"
          className="md:hidden text-2xl focus:outline-none"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Abrir menu"
        >
          ☰
        </button>

        <nav
          className={
            `${menuOpen ? 'flex' : 'hidden'}
            absolute top-full left-0 right-0 bg-gray-800 px-4 pb-4 md:static md:flex md:p-0`
          }
        >
          <ul className="menu-list flex flex-col gap-3 w-full md:flex-row md:items-center md:gap-6">
            {navItems.map((item) => (
              <li key={item.href} className="menu-item">
                <a
                  href={item.href}
                  className="text-white hover:text-gray-300 block py-1 md:py-0"
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}

export default Header;