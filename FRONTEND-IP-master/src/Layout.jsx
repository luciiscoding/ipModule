import {Header} from "../src/components/Header/Header"
import {Navbar}  from "../src/components/Navbar/Navbar"


export const Layout = ({children, headerIamge}) => {
    return(
        <>
            <Navbar />
            <Header headerIamge={headerIamge}/>
            {
                children
            }
            {/* add footer component */}
        </>
    )
}