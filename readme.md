# Plugin QGIS "CreationMap"

## Objectif

Le plugin "CreationMap" a pour but de faciliter la création de cartes représentant la densité des communes dans une région sélectionnée.

## Fonctionnement

1. **Sélection des Couches en Entrée**:
   - L'utilisateur choisit la couche contenant les communes françaises.
   - La couche de données de population est également sélectionnée.

2. **Jointure des Champs**:
   - L'utilisateur spécifie les champs de jointure entre les deux couches sélectionnées.

3. **Choix de la Région**:
   - Sélection de la région souhaitée par l'utilisateur à partir d'une liste dynamique basée sur les valeurs de la colonne "region" de la couche des communes.

4. **Résultat**:
   - Une carte est générée, montrant la densité des communes de la région choisie.
   - La symbologie utilisée est graduée comme suit :
     - Moins de 100 hab/km² : Densité Faible (Jaune)
     - Entre 100 et 200 hab/km² : Densité Moyenne (Orange)
     - Plus de 200 hab/km² : Densité Forte (Rouge)
   - Les centroïdes de chaque commune sont affichés au-dessus de celles-ci.

## Utilisation

1. Ouvrez QGIS.
2. Activez le plugin "CreationMap" sur QGIS.
3. Suivez les étapes pour sélectionner les couches, les champs de jointure et la région désirée.
4. La carte de densité des communes sera générée automatiquement.

## Exemple d'Utilisation

Voici un exemple d'utilisation du plugin "CreationMap" pour créer une carte de densité des communes en France :

1. Sélectionnez la couche des communes françaises.
2. Choisissez la couche de données de population.
3. Spécifiez les champs de jointure appropriés.
4. Sélectionnez la région "Île-de-France".
5. La carte de densité des communes de l'Île-de-France sera générée avec la symbologie spécifiée.

## Remarque

Veuillez vous assurer que les données des communes, comprenant un champ "region" spécifiant la région de chaque commune, ainsi que les donnée de population, sont correctement géoréférencées. Veillez également à ce que les champs de jointure sélectionnés soient en accord avec les données disponibles.
