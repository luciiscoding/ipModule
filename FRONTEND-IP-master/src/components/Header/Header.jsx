import './Header.css';
export const Header = ({headerIamge}) => {
    return(
        <div style={{backgroundImage: `url(${headerIamge})`}} id="header-container" className="header-container"></div>
    )
}