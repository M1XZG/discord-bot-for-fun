---
title: Fish Catalog
permalink: /features/fishing-fish-catalog
---
{% comment %}Inlined from docs/FEATURES/fishing-fish-catalog.md{% endcomment %}
{% assign fish_assets = '/FishingGameAssets' %}
# 🐟 Fishing Game Fish Catalog

An automatically generated, responsive visual catalog of all fish and special items in the fishing mini‑game.

> Data source: `_data/fish.json` (derived from the runtime config). Add or remove fish there (and supply the corresponding image) and this page updates on next build.

## Legend
- Rarity Order (rarest → most common): Mythic → Ultra-Legendary → Legendary → Epic → Rare → Uncommon → Common → Junk
- Image filename must exactly match the fish `name` (case-sensitive in repo) + extension (`.png` preferred).

---

<div class="fish-grid-wrapper">
{% assign rarity_order = site.data.fish.rarity_order %}
{% assign labels = site.data.fish.rarity_labels %}
{% for rarity in rarity_order %}
	{% assign cards = site.data.fish.items | where: 'rarity', rarity %}
	{% if cards.size > 0 %}
	<section class="fish-rarity-section" id="rarity-{{ rarity }}">
		<h2 class="fish-rarity-heading">{{ labels[rarity] }} <span class="rarity-tag">{{ cards.size }} item{% if cards.size != 1 %}s{% endif %}</span></h2>
		<div class="fish-grid">
			{% for f in cards %}
				{% capture img_path %}{{ fish_assets | relative_url }}/{{ f.name }}.png{% endcapture %}
						<article class="fish-card {{ rarity }}" aria-label="{{ f.name }} ({{ labels[rarity] }})">
					<div class="fish-meta">{{ labels[rarity] }}</div>
					<div class="fish-img-wrapper">
						<img src="{{ img_path }}" alt="{{ f.name }} image" loading="lazy" onerror="this.closest('.fish-card').classList.add('missing');" />
					</div>
					<h3 class="fish-name" id="fish-{{ f.name }}">{{ f.name }}</h3>
					<p class="fish-blurb">{{ f.blurb }}</p>
							{% if f.min_size_cm and f.max_size_cm %}
							<div class="fish-stats">
								<span>Size {{ f.min_size_cm }}–{{ f.max_size_cm }} cm</span>
								{% if f.min_weight_kg and f.max_weight_kg %}<span>Weight {{ f.min_weight_kg }}–{{ f.max_weight_kg }} kg</span>{% endif %}
							</div>
							{% endif %}
				</article>
			{% endfor %}
		</div>
	</section>
	{% endif %}
{% endfor %}

	{% assign special = site.data.fish.items | where: 'rarity', 'special' %}
	{% if special.size > 0 %}
	<section class="fish-rarity-section" id="rarity-special">
		<h2 class="fish-rarity-heading">Special <span class="rarity-tag">{{ special.size }}</span></h2>
		<div class="fish-grid">
			{% for f in special %}
				{% capture img_path %}{{ fish_assets | relative_url }}/{{ f.name }}.png{% endcapture %}
						<article class="fish-card special" aria-label="{{ f.name }} (Special)">
					<div class="fish-meta">Special</div>
					<div class="fish-img-wrapper">
						<img src="{{ img_path }}" alt="{{ f.name }} image" loading="lazy" onerror="this.closest('.fish-card').classList.add('missing');" />
					</div>
					<h3 class="fish-name" id="fish-{{ f.name }}">{{ f.name }}</h3>
					<p class="fish-blurb">{{ f.blurb }}</p>
							{% if f.min_size_cm and f.max_size_cm %}
							<div class="fish-stats">
								<span>Size {{ f.min_size_cm }}–{{ f.max_size_cm }} cm</span>
								{% if f.min_weight_kg and f.max_weight_kg %}<span>Weight {{ f.min_weight_kg }}–{{ f.max_weight_kg }} kg</span>{% endif %}
							</div>
							{% endif %}
				</article>
			{% endfor %}
		</div>
	</section>
	{% endif %}
</div>

---
### Maintenance Workflow
1. Drop new image into `FishingGameAssets/` (PNG preferred, transparent where possible).
2. Add entry to `_data/fish.json` (keep rarity consistent with game config).
3. Commit & push: GitHub Pages will rebuild automatically.
4. (Optional) Update game config / migrations if introducing new rarity or behavior.

> Member catches (avatars) are dynamic and not listed here.

---
*This page is auto-generated from data; avoid manual edits to individual fish entries here.*