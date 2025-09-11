# 🐟 Fishing Game Fish Catalog

A visual/reference catalog of all fish and items currently configured in the fishing mini‑game.

> Source of truth is `my_fishing_game_config.json`. This page is generated/maintained manually; update it after adding/removing fish or changing rarities.

## Legend
- **Rarity Order (rarest → most common):** Mythic → Ultra-Legendary → Legendary → Epic → Rare → Uncommon → Common → Junk
- **Image Match Rule:** Image filename must match the fish name exactly (case-insensitive) with allowed extensions: `.png`, `.jpg`, `.jpeg`, `.gif`.

---
## Mythic
| Image | Name | Notes |
|-------|------|-------|
| ![Helios-Sunfish](../../FishingGameAssets/Helios-Sunfish.png) | Helios-Sunfish | Blazes with a corona when landed. |

## Ultra-Legendary
| Image | Name | Notes |
|-------|------|-------|
| ![Diamond-Ring](../../FishingGameAssets/Diamond-Ring.png) | Diamond-Ring | Lost treasure; massive point potential. |

## Legendary
| Image | Name | Notes |
|-------|------|-------|
| ![Blue-Whale](../../FishingGameAssets/Blue-Whale.png) | Blue-Whale | Largest creature. |
| ![Clockwork-Carp](../../FishingGameAssets/Clockwork-Carp.png) | Clockwork-Carp | Mechanical mystery. |

## Epic
| Image | Name | Notes |
|-------|------|-------|
| ![Great-White-Shark](../../FishingGameAssets/Great-White-Shark.png) | Great-White-Shark | Apex predator. |
| ![Hammerhead-Shark](../../FishingGameAssets/Hammerhead-Shark.png) | Hammerhead-Shark | Wide head sensory boost. |
| ![Narwhal](../../FishingGameAssets/Narwhal.png) | Narwhal | Unicorn of the sea. |
| ![Lavender-Braid-Eel](../../FishingGameAssets/Lavender-Braid-Eel.png) | Lavender-Braid-Eel | Shimmering violet ribbon. |
| ![DevOps-Ducky](../../FishingGameAssets/DevOps-Ducky.png) | DevOps-Ducky | Silently debugs you. |

## Rare
| Image | Name | Notes |
|-------|------|-------|
| ![Barracuda](../../FishingGameAssets/Barracuda.png) | Barracuda | Fast strike hunter. |
| ![Mahi-Mahi](../../FishingGameAssets/Mahi-Mahi.png) | Mahi-Mahi | Acrobatic golden fighter. |
| ![Marlin](../../FishingGameAssets/Marlin.png) | Marlin | Trophy billfish. |
| ![Sailfish](../../FishingGameAssets/Sailfish.png) | Sailfish | Fastest fish. |
| ![Tarpon](../../FishingGameAssets/Tarpon.png) | Tarpon | Silver King. |
| ![Wahoo](../../FishingGameAssets/Wahoo.png) | Wahoo | Razor speed. |
| ![Starfall-Salmon](../../FishingGameAssets/Starfall-Salmon.png) | Starfall-Salmon | Meteor-shower scales. |

## Uncommon
| Image | Name | Notes |
|-------|------|-------|
| ![Sea-Bass](../../FishingGameAssets/Sea-Bass.png) | Sea-Bass | Versatile predator. |
| ![Smallmouth-Bass](../../FishingGameAssets/Smallmouth-Bass.png) | Smallmouth-Bass | Aerial fighter. |
| ![Bonefish](../../FishingGameAssets/Bonefish.png) | Bonefish | Gray ghost. |
| ![Comfy-Catfish](../../FishingGameAssets/Comfy-Catfish.png) | Comfy-Catfish | Purrs when held. |
| ![Tuna](../../FishingGameAssets/Tuna.png) | Tuna | Endurance swimmer. |

## Common
| Image | Name | Notes |
|-------|------|-------|
| ![Blue-Tang](../../FishingGameAssets/Blue-Tang.png) | Blue-Tang | Friendly reef fish. |
| ![Butterfly-fish](../../FishingGameAssets/Butterfly-fish.png) | Butterfly-fish | Patterned beauty. |
| ![Clown-Fish](../../FishingGameAssets/Clown-Fish.png) | Clown-Fish | Anemone companion. |
| ![Crab](../../FishingGameAssets/Crab.png) | Crab | Sideways scuttler. |
| ![Lobster](../../FishingGameAssets/Lobster.png) | Lobster | Prized delicacy. |
| ![Parrot-Fish](../../FishingGameAssets/Parrot-Fish.png) | Parrot-Fish | Sand maker. |
| ![Perch](../../FishingGameAssets/Perch.png) | Perch | Freshwater striped. |
| ![Sea-Cucumber](../../FishingGameAssets/Sea-Cucumber.png) | Sea-Cucumber | Regenerative oddity. |
| ![Seahorse](../../FishingGameAssets/Seahorse.png) | Seahorse | Male broods young. |
| ![Shrimp](../../FishingGameAssets/Shrimp.png) | Shrimp | Vital link species. |
| ![Starfish](../../FishingGameAssets/Starfish.png) | Starfish | Regrows limbs. |
| ![Sea-Urchin](../../FishingGameAssets/Sea-Urchin.png) | Sea-Urchin | Reef balancer. |
| ![Button-Shield-Minnow](../../FishingGameAssets/Button-Shield-Minnow.png) | Button-Shield-Minnow | Tiny & collectible. |
| ![Tangled-Headset](../../FishingGameAssets/Tangled-Headset.png) | Tangled-Headset | +5 comedy. |

## Junk
| Image | Name | Notes |
|-------|------|-------|
| ![Stinky-Boot](../../FishingGameAssets/Stinky-Boot.png) | Stinky-Boot | Putrid footwear. |
| ![Worn-Trainers](../../FishingGameAssets/Worn-Trainers.png) | Worn-Trainers | Ancient sneakers. |

---
## Special / Non-Fish
| Image | Token | Notes |
|-------|-------|-------|
| ![No-Fish](../../FishingGameAssets/No-Fish.png) | No Catch | Shown when nothing bites (consolation message). |

> Member catches use the caught user's Discord avatar (no static asset file).

---
### Maintenance Checklist
- [ ] After adding a fish via `!addfish`, add row here.
- [ ] Ensure image dropped into `FishingGameAssets/`.
- [ ] Keep rarity group sections in rarity order.
- [ ] When renaming a fish: update config JSON, asset filename, and this catalog.

*Generated manually – update as part of release notes when fish set changes.*
