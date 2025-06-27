from pydantic import BaseModel, validator
from datetime import datetime

class IrrigationInput(BaseModel):
    culture: str
    type_sol: str
    saison: str
    type_irrigation: str

class IrrigationOutput(BaseModel):
    id: int
    culture: str
    type_sol: str
    saison: str
    type_irrigation: str
    frequence_irrigation: int
    besoin_brut: str       # formaté avec unité
    besoin_par_seance: str # formaté avec unité
    irrigation_necessaire: bool
    timestamp: datetime

    @validator("besoin_brut", "besoin_par_seance", pre=True)
    def format_m3_ha_correct(cls, v, values, field):
        # si c'est déjà une chaîne, on ne touche pas
        if isinstance(v, str):
            return v
        suffix = "m³/ha/jour" if field.name == "besoin_brut" else "m³/ha"
        return f"{round(v, 2)} {suffix}"

    class Config:
        orm_mode = True
