function StudentAnswersDashboardBlock(runtime, element) {
    'use strict';
    var $element = $(element);

    // Pagination

    var Result = Backbone.Model.extend({

        initialize: function(attrs, options) {
            _.each(_.zip(Result.properties, options.values), function(pair) {
                this.set(pair[0], pair[1]);
            }, this);
        }

    }, { properties: ['section', 'subsection', 'unit', 'type', 'question', 'answer', 'username'] });

    var Results = Backbone.PageableCollection.extend({

        model: Result,

        getCurrentPage: function(object) {
            var currentPage = this.state.currentPage;
            if (object) {
                return this.getPage(currentPage);
            }
            return currentPage;
        },

        getTotalPages: function() {
            return this.state.totalPages;
        }

    });

    var ResultsView = Backbone.View.extend({

        render: function() {
            this._insertRecords(this.collection.getCurrentPage(true));
            this._updateControls();
            this.$('#total-pages').text(this.collection.getTotalPages() || 0);
            return this;
        },

        _insertRecords: function(records) {
            var tbody = this.$('tbody');
            tbody.empty();
            records.each(function(result, index) {
                var row = $('<tr>');
                if (index % 2 === 0) {
                    row.addClass('even');
                }
                _.each(Result.properties, function(name) {
                    row.append($('<td>').text(result.get(name)));
                });
                tbody.append(row);
            }, this);
            if (this.collection.getTotalPages()) {
                this.$('#current-page').text(this.collection.getCurrentPage());
            } else {
                this.$('#current-page').text(0);
            }
        },

        events: {
            'click #first-page': '_firstPage',
            'click #prev-page': '_prevPage',
            'click #next-page': '_nextPage',
            'click #last-page': '_lastPage'
        },

        _firstPage: function() {
            this._insertRecords(this.collection.getFirstPage());
            this._updateControls();
        },

        _prevPage: function() {
            if (this.collection.hasPreviousPage()) {
                this._insertRecords(this.collection.getPreviousPage());
            }
            this._updateControls();
        },

        _nextPage: function() {
            if (this.collection.hasNextPage()) {
                this._insertRecords(this.collection.getNextPage());
            }
            this._updateControls();
        },

        _lastPage: function() {
            this._insertRecords(this.collection.getLastPage());
            this._updateControls();
        },

        _updateControls: function() {
            var currentPage = this.collection.getCurrentPage(),
                totalPages = this.collection.getTotalPages(),
                firstPage = '#first-page',
                prevPage = '#prev-page',
                nextPage = '#next-page',
                lastPage = '#last-page',
                all = [firstPage, prevPage, nextPage, lastPage],
                backward = [firstPage, prevPage],
                forward = [nextPage, lastPage];
            if (!totalPages || totalPages === 1) {
                this._disable(all);
            } else {
                if (currentPage === 1) {
                    this._disable(backward);
                    this._enable(forward);
                } else if (currentPage === totalPages) {
                    this._enable(backward);
                    this._disable(forward);
                } else {
                    this._enable(all);
                }
            }
        },

        _enable: function(controls) {
            _.each(controls, function(control) {
                this.$(control).prop('disabled', false);
            }, this);
        },

        _disable: function(controls) {
            _.each(controls, function(control) {
                this.$(control).prop('disabled', true);
            }, this);
        }

    });

    var resultsView = new ResultsView({
        collection: new Results([], { mode: "client", state: { pageSize: 15 } }),
        el: $element.find('#results')
    });

    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
        window.ngettext = function ngettext_stub(strA, strB, n) { return n == 1 ? strA : strB; };
    }
    var $startButton = $element.find('.data-export-start');
    var $cancelButton = $element.find('.data-export-cancel');
    var $downloadButton = $element.find('.data-export-download');
    var $deleteButton = $element.find('.data-export-delete');
    var $blockTypes = $element.find("select[name='block_types']");
    var $rootBlockId = $element.find("input[name='root_block_id']");
    var $username = $element.find("input[name='username']");
    var $matchString = $element.find("input[name='match_string']");
    var $resultTable = $element.find('.data-export-results');

    var status;
    function getStatus() {
        $.ajax({
            type: 'POST',
            url: runtime.handlerUrl(element, 'get_status'),
            data: '{}',
            success: updateStatus,
            dataType: 'json'
        });
    }

    function updateStatus(newStatus) {
        var statusChanged = ! _.isEqual(newStatus, status);
        status = newStatus;
        if (status.export_pending) {
            // Keep polling for status updates when an export is running.
            setTimeout(getStatus, 1000);
        }
        if (statusChanged) updateView();
    }

    function showSpinner() {
        $startButton.prop('disabled', true);
        $cancelButton.prop('disabled', true);
        $downloadButton.prop('disabled', true);
        $deleteButton.prop('disabled', true);
        $('.data-export-status', $element).empty().append(
            $('<i>').addClass('icon fa fa-spinner fa-spin')
        ).css("text-align", "center");
    }

    function hideResults() {
        $resultTable.hide();
    }

    function showResults() {
        $resultTable.show();
    }

    function maybeShowResults() {
        if (status.last_export_result) {
            showResults();
        }
    }

    function handleError(data) {
        // Shim to make the XBlock JsonHandlerError response work with our format.
        status = {'last_export_result': JSON.parse(data.responseText), 'export_pending': false};
        updateView();
    }

    function updateView() {
        var $exportInfo = $('.data-export-info', $element),
            $statusArea = $('.data-export-status', $element), startTime;
        $statusArea.empty();
        $exportInfo.empty();
        $startButton.toggle(!status.export_pending).prop('disabled', false);
        $cancelButton.toggle(status.export_pending).prop('disabled', false);
        $downloadButton.toggle(Boolean(status.download_url)).prop('disabled', false);
        $deleteButton.toggle(Boolean(status.last_export_result)).prop('disabled', false);
        if (status.last_export_result) {
            if (status.last_export_result.error) {
                $statusArea.append($('<p>').text(
                    _.template(
                        gettext('Data export failed. Reason: <%= error %>'),
                        {'error': status.last_export_result.error}
                    )
                ));
                hideResults();
            } else {
                startTime = new Date(status.last_export_result.start_timestamp * 1000);
                $exportInfo.append($('<p>').text(
                    _.template(
                        ngettext(
                            'Results retrieved on <%= creation_time %> (<%= seconds %> second).',
                            'Results retrieved on <%= creation_time %> (<%= seconds %> seconds).',
                            status.last_export_result.generation_time_s.toFixed(1)
                        ),
                        {
                            'creation_time': startTime.toString(),
                            'seconds': status.last_export_result.generation_time_s.toFixed(1)
                        }
                    )
                ));

                // Display results
                var results = _.map(status.last_export_result.display_data, function(row) {
                    return new Result(null, { values: row });
                });

                resultsView.collection.fullCollection.reset(results);
                resultsView.render();

                showResults();
            }
        } else {
            if (status.export_pending) {
                $statusArea.append($('<p>').text(
                    gettext('The report is currently being generated…')
                ));
            }
        }
    }

    function addHandler($button, handlerName, form_submit) {
        $button.on('click', function() {
            var data;
            if (form_submit) {
                data = {
                    block_types: $blockTypes.val(),
                    root_block_id: $rootBlockId.val(),
                    username: $username.val(),
                    match_string: $matchString.val()
                };
                data = JSON.stringify(data);
            } else {
                data = '{}';
            }
            $.ajax({
                type: 'POST',
                url: runtime.handlerUrl(element, handlerName),
                data: data,
                success: updateStatus,
                error: handleError,
                dataType: 'json'
            });
            showSpinner();
        });
    }

    addHandler($startButton, 'start_export', true);
    addHandler($cancelButton, 'cancel_export');
    addHandler($deleteButton, 'delete_export');

    $startButton.on('click', hideResults);
    $cancelButton.on('click', maybeShowResults);
    $deleteButton.on('click', hideResults);

    $downloadButton.on('click', function() {
        window.location.href = status.download_url;
    });

    showSpinner();
    getStatus();

}
