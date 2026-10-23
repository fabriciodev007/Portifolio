import { Outlet } from 'react-router';
import Header from './components/Header.jsx';

function DefaultLayout() {
  return (
    <div className="default-layout">
      <Header />
      <Outlet />
    </div>
  );
}

export default DefaultLayout;
