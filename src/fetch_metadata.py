# %%
import json
import os
import requests


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "metadata_set.json")


# Endpoint público para Pokémon TCG API v2 (Base Set: base1)
API_URL = "https://api.pokemontcg.io/v2/cards"



def generate_fallback_metadata():
    # Muestra local estática representativa para el set me55 correspondiente a Celebrations / 30th Anniversary
    sample_data = [
  {
    "id": "me55-1",
    "name": "Exeggcute",
    "number": "1",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-1/small"
  },
  {
    "id": "me55-3",
    "name": "Volbeat",
    "number": "3",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-3/small"
  },
  {
    "id": "me55-2",
    "name": "Alolan Exeggutor",
    "number": "2",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-2/small"
  },
  {
    "id": "me55-4",
    "name": "Illumise",
    "number": "4",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-4/small"
  },
  {
    "id": "me55-5",
    "name": "Tropius",
    "number": "5",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-5/small"
  },
  {
    "id": "me55-7",
    "name": "Cherrim",
    "number": "7",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-7/small"
  },
  {
    "id": "me55-6",
    "name": "Cherubi",
    "number": "6",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-6/small"
  },
  {
    "id": "me55-8",
    "name": "Vivillon",
    "number": "8",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-8/small"
  },
  {
    "id": "me55-9",
    "name": "Vulpix",
    "number": "9",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-9/small"
  },
  {
    "id": "me55-10",
    "name": "Ninetales",
    "number": "10",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-10/small"
  },
  {
    "id": "me55-12",
    "name": "Ho-Oh",
    "number": "12",
    "rarity": "Rare",
    "image_url": "https://images.scrydex.com/pokemon/me55-12/small"
  },
  {
    "id": "me55-11",
    "name": "Moltres",
    "number": "11",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-11/small"
  },
  {
    "id": "me55-13",
    "name": "Victini",
    "number": "13",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-13/small"
  },
  {
    "id": "me55-18",
    "name": "Articuno",
    "number": "18",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-18/small"
  },
  {
    "id": "me55-16",
    "name": "Slowpoke",
    "number": "16",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-16/small"
  },
  {
    "id": "me55-14",
    "name": "Reshiram",
    "number": "14",
    "rarity": "Rare",
    "image_url": "https://images.scrydex.com/pokemon/me55-14/small"
  },
  {
    "id": "me55-15",
    "name": "Fuecoco ex",
    "number": "15",
    "rarity": "Double Rare",
    "image_url": "https://images.scrydex.com/pokemon/me55-15/small"
  },
  {
    "id": "me55-17",
    "name": "Lapras",
    "number": "17",
    "rarity": "Common",
    "image_url": "https://images.scrydex.com/pokemon/me55-17/small"
  },
  {
    "id": "me55-20",
    "name": "Palkia",
    "number": "20",
    "rarity": "Rare",
    "image_url": "https://images.scrydex.com/pokemon/me55-20/small"
  }
    ]

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)

    print(
        f"Fallback local generado con {len(sample_data)} cartas en '{OUTPUT_FILE}'."
    )


def fetch_set_metadata(limit=50):
    print(
        f"Consultando cartas del set 'me55' (Celebrations / 30th) (límite: {limit})..."
    )

    query = "set.id:me55"
    params = {
        "q": query,
        "pageSize": limit,
        "select": "id,name,number,rarity,images",
    }
    headers = {"User-Agent": "TCG-Recognize-MVP/1.0"}

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json().get("data", [])

        normalized_cards = [
            {
                "id": card.get("id"),
                "name": card.get("name"),
                "number": card.get("number"),
                "rarity": card.get("rarity", "Special"),
                "image_url": card.get("images", {}).get("small"),
            }
            for card in data
        ]

        if not normalized_cards:
            print("La API no devolvió registros para 'me55'. Usando fallback...")
            generate_fallback_metadata()
            return

        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized_cards, f, ensure_ascii=False, indent=2)

        print(
            f"Éxito: Se guardaron {len(normalized_cards)} cartas en '{OUTPUT_FILE}'."
        )

    except requests.RequestException as e:
        print(f"Error al descargar metadata: {e}")
        print("Generando archivo fallback local para continuar...")
        generate_fallback_metadata()



if __name__ == "__main__":
    fetch_set_metadata(limit=50)


