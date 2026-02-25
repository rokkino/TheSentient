from sqlalchemy.orm import Session
from models.strategy import Strategy
from typing import List, Optional
import json

class StrategyService:
    def get_strategies(self, db: Session, user_id: int) -> List[Strategy]:
        """Get all strategies for a user"""
        return db.query(Strategy).filter(Strategy.user_id == user_id).all()

    def get_strategy(self, db: Session, strategy_id: int, user_id: int) -> Optional[Strategy]:
        """Get a specific strategy"""
        return db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == user_id).first()

    def create_strategy(self, db: Session, user_id: int, name: str, description: str, definition: dict) -> Strategy:
        """Create a new strategy"""
        # Ensure definition is stored as JSON string
        definition_str = json.dumps(definition) if isinstance(definition, dict) else definition
        
        new_strategy = Strategy(
            user_id=user_id,
            name=name,
            description=description,
            definition=definition_str
        )
        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)
        return new_strategy

    def update_strategy(self, db: Session, strategy_id: int, user_id: int, name: str = None, description: str = None, definition: dict = None) -> Optional[Strategy]:
        """Update an existing strategy"""
        strategy = self.get_strategy(db, strategy_id, user_id)
        if not strategy:
            return None
            
        if name:
            strategy.name = name
        if description is not None:
            strategy.description = description
        if definition:
            strategy.definition = json.dumps(definition) if isinstance(definition, dict) else definition
            
        db.commit()
        db.refresh(strategy)
        return strategy

    def delete_strategy(self, db: Session, strategy_id: int, user_id: int) -> bool:
        """Delete a strategy"""
        strategy = self.get_strategy(db, strategy_id, user_id)
        if not strategy:
            return False
            
        db.delete(strategy)
        db.commit()
        return True

strategy_service = StrategyService()
