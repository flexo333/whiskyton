# coding: utf-8

from flask import abort, Blueprint, redirect, render_template, request
from htmlmin.minify import html_minify
from random import choice
from sqlalchemy import desc
from whiskyton import app, db, models
from whiskyton.models import Whisky, Correlation

site_blueprint = Blueprint('site', __name__)


@site_blueprint.route('/')
def index():
    return html_minify(render_template('home.html'))


@site_blueprint.route('/search', methods=['GET', 'POST'])
def search():
    whisky = Whisky(distillery=request.args['s'])
    row = Whisky.query.filter_by(slug=whisky.get_slug()).first()
    if row is None:
        return render_template('404.html', slug=whisky)
    else:
        return redirect('/' + str(row.slug))


@site_blueprint.route('/<whisky_slug>')
def whisky_page(whisky_slug):

    # error page if whisky doesn't exist
    reference = Whisky.query.filter_by(slug=whisky_slug).first()
    if reference is None:
        return abort(404)

    # load correlations
    else:

        # query
        whiskies = Correlation.query\
            .add_entity(Whisky)\
            .filter(Correlation.reference == reference.id)\
            .filter(Correlation.r > 0.5)\
            .join(Whisky, Correlation.whisky == Whisky.id)\
            .order_by(desc(Correlation.r))\
            .limit(9)

        # if query succeeded
        if whiskies is not None:

            # build result
            title = 'Whiskies for %s lovers | %s' % (reference.distillery,
                                                     app.config['MAIN_TITLE'])
            return html_minify(render_template(
                'whiskies.html',
                main_title=title,
                whiskies=whiskies,
                reference=reference,
                count=whiskies.count(),
                result_page=True
            ))

        # if queries fail, return 404
        else:
            return abort(404)


@site_blueprint.route('/w/<whisky_id>')
def search_id(whisky_id):
    reference = Whisky.query.filter_by(id=whisky_id).first()
    if reference is None:
        return abort(404)
    else:
        return redirect('/' + reference.slug)


@site_blueprint.errorhandler(404)
def page_not_found(error):
    return html_minify(render_template('404.html', error=error)), 404


@site_blueprint.context_processor
def inject_main_vars():

    # get a random whisky (proportional to the page views)
    whisky_ids = list()
    for whisky in db.session.query(Whisky.id, Whisky.views).all():
        whisky_ids.extend([whisky.id] * whisky.views)
    print whisky_ids
    random_whisky = choice(whisky_ids)

    # return useful variables
    return {
        'main_title': app.config['MAIN_TITLE'],
        'headline': app.config['HEADLINE'],
        'remote_scripts': app.config['GOOGLE_ANALYTICS'],
        'random_one': Whisky.query.get(random_whisky)
    }