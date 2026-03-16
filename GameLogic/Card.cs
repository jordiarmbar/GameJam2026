using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class Card
{
    public enum Suit { Corazones, Diamantes, Treboles, Picas }
    public Suit suit;
    public int rank; // 1 (As), 2, 3... 11 (J), 12 (Q), 13 (K)
    
    public int baseChips;
    public int sellValue;
    public int evolutionLevel = 0;

    public Card(Suit suit, int rank)
    {
        this.suit = suit;
        this.rank = rank;
        this.sellValue = 2; // Valor base de venta
        CalculateBaseChips();
    }

    private void CalculateBaseChips()
    {
        // Al estilo Balatro: J, Q, K dan 10 fichas, As da 11. Cartas numeradas dan su valor.
        if (rank >= 2 && rank <= 10) baseChips = rank;
        else if (rank >= 11 && rank <= 13) baseChips = 10;
        else if (rank == 1) baseChips = 11;
        else baseChips = rank;
    }

    // Lógica para evolucionar la carta al final de cada ronda
    public void Evolve()
    {
        evolutionLevel++;
        rank++; // La carta 1 pasará a ser la 2, etc.
        sellValue += 3; // Su valor de venta incrementa
        baseChips += 5; // Aumentar fichas base para hacerla más poderosa
        
        // Opcional: Si el rango supera 13 (K), podemos hacerlo volver a empezar o convertirse en un tipo "Super"
        Debug.Log($"Carta evolucionada a rango {rank}. Valor de venta: {sellValue}");
    }
}
