---
title: Fish Catalog
permalink: /features/fishing-fish-catalog
---
{% comment %}Inlined from docs/FEATURES/fishing-fish-catalog.md{% endcomment %}
{% assign fish_assets = '/FishingGameAssets' %}
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
| ![Helios-Sunfish]({{ fish_assets | relative_url }}/Helios-Sunfish.png) | Helios-Sunfish | Blazes with a corona when landed. |

## Ultra-Legendary
| Image | Name | Notes |
|-------|------|-------|
| ![Diamond-Ring]({{ fish_assets | relative_url }}/Diamond-Ring.png) | Diamond-Ring | Lost treasure; massive point potential. |

## Legendary
| Image | Name | Notes |
|-------|------|-------|
| ![Blue-Whale]({{ fish_assets | relative_url }}/Blue-Whale.png) | Blue-Whale | Largest creature. |
| ![Clockwork-Carp]({{ fish_assets | relative_url }}/Clockwork-Carp.png) | Clockwork-Carp | Mechanical mystery. |

## Epic
| Image | Name | Notes |
|-------|------|-------|
| ![Great-White-Shark]({{ fish_assets | relative_url }}/Great-White-Shark.png) | Great-White-Shark | Apex predator. |
| ![Hammerhead-Shark]({{ fish_assets | relative_url }}/Hammerhead-Shark.png) | Hammerhead-Shark | Wide head sensory boost. |
| ![Narwhal]({{ fish_assets | relative_url }}/Narwhal.png) | Narwhal | Unicorn of the sea. |
| ![Lavender-Braid-Eel]({{ fish_assets | relative_url }}/Lavender-Braid-Eel.png) | Lavender-Braid-Eel | Shimmering violet ribbon. |
| ![DevOps-Ducky]({{ fish_assets | relative_url }}/DevOps-Ducky.png) | DevOps-Ducky | Silently debugs you. |

## Rare
| Image | Name | Notes |
|-------|------|-------|
| ![Barracuda]({{ fish_assets | relative_url }}/Barracuda.png) | Barracuda | Fast strike hunter. |
| ![Mahi-Mahi]({{ fish_assets | relative_url }}/Mahi-Mahi.png) | Mahi-Mahi | Acrobatic golden fighter. |
| ![Marlin]({{ fish_assets | relative_url }}/Marlin.png) | Marlin | Trophy billfish. |
| ![Sailfish]({{ fish_assets | relative_url }}/Sailfish.png) | Sailfish | Fastest fish. |
| ![Tarpon]({{ fish_assets | relative_url }}/Tarpon.png) | Tarpon | Silver King. |
| ![Wahoo]({{ fish_assets | relative_url }}/Wahoo.png) | Wahoo | Razor speed. |
| ![Starfall-Salmon]({{ fish_assets | relative_url }}/Starfall-Salmon.png) | Starfall-Salmon | Meteor-shower scales. |

## Uncommon
| Image | Name | Notes |
|-------|------|-------|
| ![Sea-Bass]({{ fish_assets | relative_url }}/Sea-Bass.png) | Sea-Bass | Versatile predator. |
| ![Smallmouth-Bass]({{ fish_assets | relative_url }}/Smallmouth-Bass.png) | Smallmouth-Bass | Aerial fighter. |
| ![Bonefish]({{ fish_assets | relative_url }}/Bonefish.png) | Bonefish | Gray ghost. |
| ![Comfy-Catfish]({{ fish_assets | relative_url }}/Comfy-Catfish.png) | Comfy-Catfish | Purrs when held. |
| ![Tuna]({{ fish_assets | relative_url }}/Tuna.png) | Tuna | Endurance swimmer. |

## Common
| Image | Name | Notes |
|-------|------|-------|
| ![Blue-Tang]({{ fish_assets | relative_url }}/Blue-Tang.png) | Blue-Tang | Friendly reef fish. |
| ![Butterfly-fish]({{ fish_assets | relative_url }}/Butterfly-fish.png) | Butterfly-fish | Patterned beauty. |
| ![Clown-Fish]({{ fish_assets | relative_url }}/Clown-Fish.png) | Clown-Fish | Anemone companion. |
| ![Crab]({{ fish_assets | relative_url }}/Crab.png) | Crab | Sideways scuttler. |
| ![Lobster]({{ fish_assets | relative_url }}/Lobster.png) | Lobster | Prized delicacy. |
| ![Parrot-Fish]({{ fish_assets | relative_url }}/Parrot-Fish.png) | Parrot-Fish | Sand maker. |
| ![Perch]({{ fish_assets | relative_url }}/Perch.png) | Perch | Freshwater striped. |
| ![Sea-Cucumber]({{ fish_assets | relative_url }}/Sea-Cucumber.png) | Sea-Cucumber | Regenerative oddity. |
| ![Seahorse]({{ fish_assets | relative_url }}/Seahorse.png) | Seahorse | Male broods young. |
| ![Shrimp]({{ fish_assets | relative_url }}/Shrimp.png) | Shrimp | Vital link species. |
| ![Starfish]({{ fish_assets | relative_url }}/Starfish.png) | Starfish | Regrows limbs. |
| ![Sea-Urchin]({{ fish_assets | relative_url }}/Sea-Urchin.png) | Sea-Urchin | Reef balancer. |
| ![Button-Shield-Minnow]({{ fish_assets | relative_url }}/Button-Shield-Minnow.png) | Button-Shield-Minnow | Tiny & collectible. |
| ![Tangled-Headset]({{ fish_assets | relative_url }}/Tangled-Headset.png) | Tangled-Headset | +5 comedy. |

## Junk
| Image | Name | Notes |
|-------|------|-------|
| ![Stinky-Boot]({{ fish_assets | relative_url }}/Stinky-Boot.png) | Stinky-Boot | Putrid footwear. |
| ![Worn-Trainers]({{ fish_assets | relative_url }}/Worn-Trainers.png) | Worn-Trainers | Ancient sneakers. |

---
## Special / Non-Fish
| Image | Token | Notes |
|-------|-------|-------|
| ![No-Fish]({{ fish_assets | relative_url }}/No-Fish.png) | No Catch | Shown when nothing bites (consolation message). |

> Member catches use the caught user's Discord avatar (no static asset file).

---
### Maintenance Checklist
- [ ] After adding a fish via `!addfish`, add row here.
- [ ] Ensure image dropped into `FishingGameAssets/`.
- [ ] Keep rarity group sections in rarity order.
- [ ] When renaming a fish: update config JSON, asset filename, and this catalog.

*Generated manually – update as part of release notes when fish set changes.*