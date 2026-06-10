import { Outlet } from "react-router-dom";
import Navbar from "@/components/Navbar/NavbarGoogle";
import Footer from "@/components/Footer";

function MainLayout() {
  return (
    <>
      <Navbar />
      <Outlet />
      <Footer />
    </>
  );
}

export default MainLayout;
