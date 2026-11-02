# Radar Dragon Ball — écran Waveshare ESP32-S3-Touch-AMOLED-1.43

Boîtier du radar Dragon Ball (remix du modèle MakerWorld 2776400) pour la carte Waveshare
ESP32-S3-Touch-AMOLED-1.43, avec une LiPo 603040 sous la carte et une molette qui appuie sur le
bouton BOOT. Dimensions : Ø 57,6 × 21,4 mm.

## Fichiers

- `dragon-radar-1.43.3mf` : projet Bambu Studio (X2D, buse 0.4, 0,20 mm, plaque PEI texturée),
  un seul plateau, ~1 h 20. Filament 1 = radar et support, filament 2 = logo.
- `stl/`, `step/` : chaque pièce séparée (face, dos, logo, molette, berceau, support).
- `images/` : rendus, coupes, couleurs du logo. `dimensions.json` : toutes les cotes.

## Impression

- Face **lèvre en haut**, comme dans le 3MF. Ne la retourne pas : posée sur sa face avant, tout le
  dôme visible devient un surplomb couvert de supports.
- Supports seulement sous la lèvre (l'appui de la vitre, caché par l'écran), dans le filament de
  la face avec 0,2 mm d'écart. Option plus propre : interface de support en PETG (distance Z
  supérieure 0) ; PLA et PETG ne collent pas entre eux.
- Dos : fond sur le plateau, logo incrusté dans les 3 premières couches (2e couleur). Sans 2e
  couleur, supprime la pièce « logo » : il reste gravé en creux.
- Molette : roue en bas.

## Visserie (M2)

- 4 × M2×5 tête fraisée : carte sur le berceau, dans les entretoises laiton, par-dessous.
- 3 × M2×6 tête fraisée : berceau sur les plots du dos, par-dessus.
- 6 × M2×10 tête cylindrique ou bombée : fermeture, par le dos.

## Montage

1. Visse la carte sur le berceau (4 × M2×5 fraisées, par-dessous).
2. Colle la batterie au fond du dos (adhésif double face).
3. Vérifie la polarité au multimètre avant de brancher sur BAT (connecteur 1,25 mm 2 broches) ;
   la fiche se branche par l'intérieur de la carte.
4. Pose le berceau sur les 3 plots et visse-le (3 × M2×6 fraisées).
5. Pose la molette : bride carrée dans la demi-cavité carrée, lame plate dans sa fente.
6. Ferme avec la face (la molette est prise entre les deux coques) et visse les 6 × M2×10 par le
   dos. Les plots du berceau sont volontairement 0,1 mm trop hauts : la vitre est plaquée sous la lèvre.

## Molette et firmware

- Appui court : zoom suivant (sur un écran éteint ou en veille, l'appui le réveille seulement).
- Appui long (2 s) : l'anneau rouge se remplit, puis au relâchement le radar passe en veille profonde.
- Réveil : tenir la molette 1,5 s. Un choc le renvoie en veille.
- Rotation de l'écran (page web du radar) : 335° avec ce boîtier.
- Pas de vraie coupure : la LED d'alimentation de la carte reste allumée en veille.
- Molette tenue au branchement USB ou au reset : la carte démarre en mode programmation ;
  relâche et refais un reset.
