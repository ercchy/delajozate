import re
import sunburnt
import settings

solr = sunburnt.SolrInterface(settings.SOLR_URL)
re_id_strip = re.compile(r'[^\d]+')

def query_for_id(query, type=None, rows=15):
	if type:
		results = solr.query(query).filter(tip=type).paginate(rows=rows).field_limit(fields=["ime", "id"]).execute()
	else:
		results = solr.query(query).paginate(rows=rows).field_limit(fields=["ime", "id"]).execute()
	return [{"ime": doc.get("ime", ""), "id": re_id_strip.sub('', doc.get("id", ""))} for doc in results.result.docs]


def query_texts(query, type, highlight=False, facet=False, rows=15):
	# Common query parameters
	query = solr.query(query).filter(tip=type).paginate(rows=rows)
	if highlight:
		query = query.highlight(fields=["ime", "besedilo"])

	if type == "zapis":
		query = query.field_limit(["id", "seja_id", "zasedanje_id", "govorec", "datum", "besedilo"])
		if facet:
			query = query.facet_by("seja_id").facet_by("zasedanje_id").facet_by("govorec").facet_by("datum")
	elif type == "zasedanje":
		query = query.field_limit(["id", "seja_id", "datum"])
		if facet:
			query = query.facet_by("datum").facet_by("seja_id")
	query_results = query.execute()

	results = { "documents" : {} }
	for document in query_results.result.docs:
		results["documents"][re_id_strip.sub('', document["id"])] = document

	if highlight:
		for id in query_results.highlighting:
			results["documents"][re_id_strip.sub('', id)].update({ "highlight": query_results.highlighting[id] })

	if facet:
		results["facets"] = query_results.facet_counts.facet_fields
	return results