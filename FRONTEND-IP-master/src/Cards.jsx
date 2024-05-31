import React, { useState, useEffect } from 'react';
import './Cards.css';
import Modal from './modal';

function Cards({ recipe }) {
  const [modalOpen, setModalOpen] = useState(false);

  const toggleModal = () => {
    setModalOpen(!modalOpen);
  };

  useEffect(() => {
    if (modalOpen) {
      document.body.classList.add('no-scroll');
    } else {
      document.body.classList.remove('no-scroll');
    }
  }, [modalOpen]);

  const imageSrc = (recipe.imageList && recipe.imageList.length > 0) ? recipe.imageList[0] : 'defaultImage.jpg';

  return(
    <div className="card">
      <img src={imageSrc} alt={recipe.recipeTitle} className="card-img"/>
      <div className="card-body">
        <h5 className="card-title">{recipe.recipeTitle}</h5>
        <button className="btn btn-primary" onClick={toggleModal}>Details</button>
      </div>
      {modalOpen && <Modal recipe={recipe} toggleModal={toggleModal} />}
    </div>
  );
}

export default Cards;