import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import classNames from 'classnames';

import {
  resetState,
  invalidateRates,
} from '../actions';

import histogramToImg from '../histogram-to-img';

import { trackEvent } from '../../common/ga';
import Description from './description';
import Highlights from './highlights';
import Histogram from './histogram';
import ExportData from './export-data';
import ResultsTable from './results-table';
import LoadableOptionalFilters from './optional-filters/loadable-optional-filters';
import LoadableScheduleFilter from './optional-filters/loadable-schedule-filter';
import LoadableContractYearFilter from './optional-filters/loadable-contract-year-filter';
import LaborCategory from './labor-category';
import LoadingIndicator from './loading-indicator';
import TitleTagSynchronizer from './title-tag-synchronizer';

import { autobind } from '../util';

class App extends React.Component {
  constructor(props) {
    super(props);
    autobind(this, [
      'handleSubmit',
      'handleResetClick',
      'handleDownloadClick',
    ]);
  }

  getContainerClassNames() {
    let loaded = false;
    let loading = false;
    let error = false;

    if (this.props.ratesInProgress) {
      loading = true;
    } else if (this.props.ratesError) {
      if (this.props.ratesError !== 'abort') {
        error = true;
        loaded = true;
      }
    } else {
      loaded = true;
    }

    return {
      search: true,
      content: true,
      container: true,
      loaded,
      loading,
      error,
    };
  }

  handleSubmit(e) {
    e.preventDefault();
    this.props.invalidateRates();
  }

  handleResetClick(e) {
    e.preventDefault();
    this.props.resetState();
  }

  handleDownloadClick(e) {
    e.preventDefault();
    histogramToImg(
      this.histogram.getWrappedInstance().svgEl,
      this.canvasEl,
    );
    trackEvent('download-graph', 'click');
  }

  render() {
    const prefixId = name => `${this.props.idPrefix}${name}`;

    return (
      <form
        id={prefixId('search')}
        className={classNames(this.getContainerClassNames())}
        onSubmit={this.handleSubmit}
        role="form"
      >
        <div className="row">
          <div className="search-header columns twelve">
            <h2>Search labor categories</h2>
            <p>
              Enter your search terms below, separated by commas.
              {' '}
              (For example: Engineer, Consultant)
            </p>
          </div>
        </div>
        <div className="row">
          <div className="columns twelve">
            <TitleTagSynchronizer />
            <section className="search">
              <div className="container clearfix">
                <LaborCategory api={this.props.api}>
                  <LoadableScheduleFilter />
                  <button className="submit usa-button-primary icon-search" />
                  {' '}
                </LaborCategory>
              </div>
              <expandable-area>
                <LoadableOptionalFilters />
              </expandable-area>
            </section>
          </div>
        </div>
        <div className="row clearfix">
          <div className="columns nine">
            <div className="graph-block">
              {/* for converting the histogram into an img --> */}
              <canvas
                ref={(el) => { this.canvasEl = el; }}
                id={prefixId('graph') /* Selenium needs it. */}
                className="hidden" width="710" height="280"
              />

              <div id={prefixId('description')}>
                <Description />
              </div>

              <h4>Hourly rate data</h4>

              <LoadingIndicator />

              <div className="graph">
                <div id={prefixId('price-histogram')}>
                  <Histogram ref={(el) => { this.histogram = el; }} />
                </div>
              </div>

              <div className="download-buttons row">
                <div className="four columns">
                  <a
                    className="usa-button usa-button-primary"
                    id={prefixId('download-histogram') /* Selenium needs it. */}
                    href=""
                    onClick={this.handleDownloadClick}
                  >
                    ⬇ Download graph
                  </a>
                </div>

                <div>
                  <ExportData />
                </div>
                <p className="help-text">
                  The rates shown here are fully burdened, applicable
                  {' '}
                  worldwide, and representative of the current fiscal
                  {' '}
                  year. This data represents rates awarded at the master
                  {' '}
                  contract level.
                </p>
              </div>
            </div>
          </div>
          <div className="columns three">
            <Highlights />
          </div>
        </div>
        <div className="row clearfix">
          <div className="filter-container columns three">
            <div className="filter-block">
              <h5 className="filter-title">Optional filters</h5>
              <LoadableContractYearFilter />
            </div>
          </div>
        </div>
        <section className="results">
          <div className="container">
            <div className="row">
              <div className="table-container">
                <ResultsTable />
              </div>
            </div>
          </div>
        </section>
      </form>
    );
  }
}

App.propTypes = {
  api: PropTypes.object.isRequired,
  ratesInProgress: PropTypes.bool.isRequired,
  ratesError: PropTypes.string,
  resetState: PropTypes.func.isRequired,
  invalidateRates: PropTypes.func.isRequired,
  idPrefix: PropTypes.string,
};

App.defaultProps = {
  idPrefix: '',
  ratesError: null,
};

export default connect(
  state => ({
    ratesInProgress: state.rates.inProgress,
    ratesError: state.rates.error,
  }),
  { resetState, invalidateRates },
)(App);
